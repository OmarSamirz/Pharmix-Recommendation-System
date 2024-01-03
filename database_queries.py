import pandas as pd
import mysql.connector as sc


db = sc.connect(
    host='pharmix-demo.cuwpxjvz89qz.eu-north-1.rds.amazonaws.com',
    user='admin',
    passwd='pharmix_sql_123',
    database='pharmix_db'
        )

mycursor = db.cursor()


def get_user_products(user_id: int) -> pd.DataFrame:
    mycursor.execute(
        """
            select product_id, total
            from User_Feedback
            where user_id = %s
            and total > 4
            order by total desc
        """, [user_id])
    
    data = mycursor.fetchall()

    result_lst = []
    for row in data:
        product_id, total_rating = row
        result_lst.append([user_id, product_id - 1, total_rating])


    df = pd.DataFrame(result_lst, columns=['user_id', 'product_id', 'total_rating'])
    
    return df


def get_feedbacks(current_user_id: int, filter_size: int, product_set: set[str]):
    mycursor.execute(
        """
            select user_id, product_id, total
            from User_Feedback
            where user_id != %s
            and total > 5
        """, [current_user_id])
    
    data = mycursor.fetchall()

    # Get users who have the same taste as us
    overlap_users = {}
    for row in data:    
        user_id, product_id, total_rating = row

        if (product_id - 1) in product_set:
            if user_id not in overlap_users:
                overlap_users[user_id] = 1
            else:
                overlap_users[user_id] += 1

    # Filter users to get the most same users as us
    product_set_length = len(product_set)
    filtered_overlap_users = set(
        [i for i in overlap_users if overlap_users[i] > product_set_length / filter_size])
    
    interactions_lst = []
    for row in data:
        user_id, product_id, total_rating = row
        if user_id in filtered_overlap_users:
            interactions_lst.append([user_id, product_id - 1, total_rating])

    interactions = pd.DataFrame(interactions_lst, columns=['user_id', 'product_id', 'total_rating'])

    return interactions

    

def get_all_products() -> pd.DataFrame:
    mycursor.execute(
        """
            select product_id, image_url, name, price, active_ingredient, company_name, volume, amount, size, concentration, is_prescription, description, category_name
            from Product left join  Category
            on Product.category_id = Category.category_id
        """
    )

    data = mycursor.fetchall()

    result_lst = []
    for row in data:
        result_lst.append([row[0] - 1, row[1], row[2], row[3],
                          row[4], row[5], row[6], row[7], 
                          row[8], row[9], row[10], row[11], 
                          row[12]])
    
    df = pd.DataFrame(result_lst, columns=['id', 'image_url', 'name', 'price', 'active_ingredient', 'company_name', 'volume', 'amount', 'size', 'concentration', 'is_prescription', 'description', 'category'])
    df.sort_values(by='id', inplace=True)
    df['tags'] = df['category'] + ' ' + df['active_ingredient'] + ' ' + df['volume'] + ' ' + df['size'] + ' ' + df['concentration']

    return df

