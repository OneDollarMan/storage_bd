from mysql.connector import connect, Error


class StorageRepo:
    ROLE_USER = 0
    ROLE_SELLER = 1
    ROLE_SUPERVISOR = 2

    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = "gmfk2ASD"
        self.database = "storage"
        self.connection = self.get_connect()
        self.cursor = self.connection.cursor()

        self.get_tables = lambda: self.raw_query("SHOW TABLES")

        self.get_user = lambda username: self.raw_query("SELECT * FROM user WHERE username='%s'" % username)
        self.login_user = lambda username, password: self.get_query(
            "SELECT * FROM user WHERE username='%s' AND password='%s'" % (username, password))
        self.add_user = lambda username, fio, password: self.write_query(
            "INSERT INTO user SET username='%s', fio='%s', password='%s', role=0" % (username, fio, password))
        self.get_all_zero_users = lambda: self.raw_query("SELECT * FROM user WHERE role=0")

        self.add_supplier = lambda name, address, phone: self.write_query(
            "INSERT INTO supplier SET name='%s', address='%s', phone='%s'" % (name, address, phone))
        self.get_suppliers = lambda: self.raw_query("SELECT * FROM supplier WHERE hidden='0'")
        self.get_supplier = lambda id: self.get_query("SELECT * FROM supplier WHERE id='%d'" % id)
        self.rm_supplier = lambda id: self.write_query("UPDATE supplier SET hidden='1' WHERE id='%d'" % id)

        self.get_products = lambda: self.raw_query(
            "SELECT * FROM product p JOIN supplier s, unit u WHERE p.supplier=s.id AND p.unit=u.id AND p.hidden='0' AND (s.hidden='0' OR p.amount > 0)")
        self.get_products_of_supplier = lambda id: self.raw_query("SELECT * FROM product WHERE supplier='%d'" % id)
        self.add_product = lambda p, n, u, b, s: self.write_query(
            "INSERT INTO product SET supplier='%s', name='%s', unit='%s', buy_price='%d', sell_price='%d'" % (
            p, n, u, b, s))
        self.add_product_amount = lambda i, a: self.write_query(
            "UPDATE product SET amount=amount+'%f' WHERE id='%d'" % (a, i))
        self.get_product = lambda id: self.get_query(
            "SELECT * FROM product p JOIN supplier s, unit u WHERE p.supplier=s.id AND p.unit=u.id AND p.id='%d'" % id)
        self.change_product_amount = lambda id, amount: self.write_query(
            "UPDATE product SET amount=amount+'%f' WHERE id='%d'" % (amount, id))
        self.rm_product = lambda id: self.write_query("UPDATE product SET hidden='1' WHERE id='%d'" % id)
        self.rm_supplier_products = lambda id: self.write_query(
            "UPDATE product SET supplier='0' WHERE supplier='%d'" % id)

        self.get_customers = lambda: self.raw_query("SELECT * FROM customer WHERE hidden='0'")
        self.add_customer = lambda n, a, p: self.write_query(
            "INSERT INTO customer SET name='%s', address='%s', phone='%s'" % (n, a, p))
        self.get_customer = lambda id: self.get_query("SELECT * FROM customer WHERE id='%d'" % id)
        self.get_sales_of_customer = lambda id: self.raw_query("SELECT * FROM sale WHERE customer='%d'" % id)
        self.rm_customer = lambda id: self.write_query("UPDATE customer SET hidden='1' WHERE id='%d'" % id)

        self.get_sales = lambda: self.raw_query(
            "SELECT * FROM sale s JOIN product p, customer c, unit u WHERE s.product=p.id AND s.customer=c.id AND p.unit=u.id")
        self.add_s = lambda c, p, a, d: self.write_query(
            "INSERT INTO SALE SET customer='%d', product='%d', amount='%f', date='%s'" % (c, p, a, d))
        self.get_sale = lambda id: self.get_query(
            "SELECT * FROM sale s JOIN customer c, product p, unit u WHERE s.customer=c.id AND s.product=p.id AND p.unit=u.id AND s.id='%d'" % id)
        self.get_sales_of_product = lambda id: self.raw_query("SELECT * FROM sale WHERE product='%d'" % id)
        self.rm_sale = lambda id: self.write_query("DELETE FROM sale WHERE id='%d'" % id)
        self.rm_customer_sales = lambda id: self.write_query("DELETE from sale WHERE customer='%d'" % id)
        self.rm_product_sales = lambda id: self.write_query("DELETE from sale WHERE product='%d'" % id)
        self.select_products_sales = lambda: self.raw_query("SELECT * FROM product p JOIN supplier s, unit u WHERE p.supplier=s.id AND p.unit=u.id AND p.id IN (SELECT product FROM sale)")

        self.get_units = lambda: self.raw_query("SELECT * FROM unit")

    def get_connect(self):
        try:
            return connect(host=self.host, user=self.user, password=self.password, database=self.database)
        except Error as e:
            print(e)

    def raw_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    def write_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            self.connection.commit()
            return self.cursor.fetchall()

    def get_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            return self.cursor.fetchone()

    def get_one_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            return self.cursor.fetchone()[0]

    def add_sale(self, c, p, a, d):
        q = self.get_one_query("SELECT amount FROM product WHERE id='%d'" % p)
        if q >= a:
            self.add_s(c, p, a, d)
            self.change_product_amount(p, -a)
            return True
        else:
            return False

    def remove_sale(self, id):
        s = self.get_sale(id)
        if s:
            self.rm_sale(id)
            self.change_product_amount(s[2], s[3])

    def get_sales_sorted(self, start_date, end_date, customer, product):
        q = "SELECT * FROM sale s JOIN product p, customer c, unit u WHERE s.product=p.id AND s.customer=c.id AND p.unit=u.id"
        if start_date:
            q = q + " AND date > '%s'" % start_date
        if end_date:
            q = q + " AND date < '%s'" % end_date
        if customer:
            q = q + " AND customer = '%d'" % int(customer)
        if product:
            q = q + " AND product = '%d'" % int(product)

        return self.raw_query(q)
