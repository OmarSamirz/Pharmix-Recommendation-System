import numpy as np
from models import *
from database_queries import *
from scipy.sparse import coo_matrix
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer


class PharmixRecommender:
    def __init__(self, value: RecommendationScheme) -> None:
        self.user_id = value.user_id
        self.n_recommend = value.n_recommend
        self._all_products = get_all_products()

    def __call__(self) -> list:
        content_based_lst = set(self._content_based())
        collaborative_filtering_lst = set(self._collaborative_filtering())

        # remove duplicates from the lists above
        # then get all the products using id 
        products_id = list(content_based_lst - collaborative_filtering_lst)
        recommended_products = self._all_products.iloc[products_id, :]

        db.close()
        
        # creating list of products to recommend
        # these products to the user
        result = [Product(product[1][0] + 1, product[1][1], product[1][2],
                          product[1][3], 0, 0, product[1][5],
                          product[1][12], product[1][7], False, False, product[1][11]) 
                        for product in recommended_products.iterrows()]
    
        return result


    def get_products(self) -> list:
        content_based_lst = set(self._content_based())
        collaborative_filtering_lst = set(self._collaborative_filtering())

        # remove duplicates from the lists above
        products_id = list(content_based_lst - collaborative_filtering_lst)
        recommended_products = self._all_products.iloc[products_id, :]

        db.close()
        
        # creating list of products to recommend 
        # these products to the user as a final result
        result = [Product(product[1][0] + 1, product[1][1], product[1][2],
                          product[1][3], 0, 0, product[1][5],
                          product[1][12], product[1][7], False, False, product[1][11]) 
                        for product in recommended_products.iterrows()]
    
        return result
    
    def _content_based(self) -> list[int]:
        # Create vectorizer model
        vectorizer = TfidfVectorizer()
        tfidf = vectorizer.fit_transform(self._all_products['tags'])

        # get all the products that
        # the user liked such that he/she puts this product 
        # in favorites, in the carts or ordered this product before
        user_products_id_lst = get_user_products(user_id=1)['product_id']
        if (len(user_products_id_lst) == 0):
            return []

        # finding similar products to the user's liked products
        # using category, active ingredient and the concentration 
        # of the active ingredient in the medicine
        similar_products_lst = []
        for product_id in user_products_id_lst:
            query_vec = vectorizer.transform([self._all_products['tags'].iloc[product_id]])
            similarity = cosine_similarity(query_vec, tfidf).flatten()
            indices = np.argpartition(similarity, -self.n_recommend)[-self.n_recommend::]
            results = self._all_products.iloc[indices]
            similar_products_lst.extend(results['id'])

        return similar_products_lst


    def _collaborative_filtering(self) -> list[int]:
        recommendation_size = 15
        user_products_lst = get_user_products(self.user_id)
        user_products_lst['product_id'] = user_products_lst['product_id'].astype(str)
        product_set = set(user_products_lst['product_id'])

        interactions = get_feedbacks(current_user_id = self.user_id, filter_size = 10,
                                     product_set = product_set)
        if (len(interactions) == 0):
            return []

        interactions = pd.concat([user_products_lst[['user_id', 'product_id', 'total_rating']], interactions])
        
        interactions['user_id'] = interactions['user_id'].astype(str)
        interactions['product_id'] = interactions['product_id'].astype(str)
        interactions['total_rating'] = pd.to_numeric(interactions['total_rating'])
        interactions['user_index'] = interactions['user_id'].astype('category').cat.codes
        interactions['product_index'] = interactions['product_id'].astype('category').cat.codes

        rating_mat_coo = coo_matrix((interactions['total_rating'], 
                                    (interactions['user_index'], interactions['product_index'])))
        rating_mat = rating_mat_coo.tocsr()

        user_index = interactions[interactions['user_id'] == str(self.user_id)]['user_index'][0].astype('int64')
        similarity = cosine_similarity(rating_mat[user_index, :], rating_mat).flatten()
        if (len(similarity) < 15):
            recommendation_size = len(similarity)
        
        indices = np.argpartition(similarity, -recommendation_size)[-recommendation_size:]
        similar_users = interactions[interactions['user_index'].isin(indices)].copy()
        similar_users = similar_users[similar_users['user_id'] != str(self.user_id)]

        product_recs = similar_users.groupby('product_id').total_rating.agg(['count', 'mean'])
        product_recs = product_recs.merge(self._all_products['product_id'], how='inner', on='product_id')
        product_recs['adjusted_count'] = product_recs['count'] * (product_recs['count'] / product_recs['total_rating'])
        product_recs['score'] = product_recs['mean'] * product_recs['adjusted_count']

        top_recs = product_recs.sort_values('score', ascending=False)

        return top_recs['product_id']
        

