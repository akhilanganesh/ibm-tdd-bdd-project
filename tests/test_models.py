# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
logger = logging.getLogger("test_models")


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.id, product.id)
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should Read a product already in the database"""
        # Create fake Product
        product = ProductFactory()
        logger.info(product)
        product.id = None
        product.create()
        # Assert that it was assigned an id
        self.assertIsNotNone(product.id)
        # Assert that the product can be read from the database and
        # check that it matches the original product
        new_product = Product.find(product.id)
        self.assertEqual(new_product.id, product.id)
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(new_product.price, product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_update_a_product(self):
        """It should Update a product already in the database"""
        # Create fake Product
        product = ProductFactory()
        logger.info(product)
        product.id = None
        product.create()
        logger.info(product)
        # Store attributes to compare with updated product
        old_id = product.id
        new_desc = "This is a new description"
        # Update product
        product.description = new_desc
        product.update()
        # Check that product is updated locally
        self.assertEqual(product.id, old_id)
        self.assertEqual(product.description, new_desc)
        # Fetch all products from the database to check that
        # there is still only one item in the database
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Assert that the fetched product is the updated product
        new_product = products[0]
        self.assertEqual(new_product.id, old_id)
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, new_desc)
        self.assertEqual(new_product.price, product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_delete_a_product(self):
        """It should Delete a product already in the database"""
        # Create fake Product
        product = ProductFactory()
        product.create()
        # Check there is one item in the database
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Delete product from database
        product.delete()
        # Check there is no items in the database
        new_products = Product.all()
        self.assertEqual(len(new_products), 0)

    def test_list_all_products(self):
        """It should list all products in the database"""
        # Check that there are no products in database at start
        products = Product.all()
        self.assertEqual(len(products), 0)
        # Create five fake Products
        for _ in range(5):
            # Create fake Product
            product = ProductFactory()
            product.create()
        # Check that there are five products in the database
        new_products = Product.all()
        self.assertEqual(len(new_products), 5)

    def test_find_product_by_name(self):
        """It should find a product in the database by name"""
        # Create five fake Products
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        # Get count of products with same name as first product
        name = products[0].name
        count_name = len([1 for product in products
                         if product.name == name])
        # Find products by the same name in the database
        new_products = Product.find_by_name(name)
        # Assert that the number of products of the same name
        # locally is equal to the number of the same name
        # in the database
        self.assertEqual(new_products.count(), count_name)
        # Check that the returned products all have the same name
        for product in new_products:
            self.assertEqual(product.name, name)

    def test_find_product_by_availability(self):
        """It should find a product in the database by availability"""
        # Create ten fake Products
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        # Get count of products with same avail. as first product
        avail = products[0].available
        count_avail = len([1 for product in products
                          if product.available == avail])
        # Find products by the same availability in the database
        new_products = Product.find_by_availability(avail)
        # Assert that the number of products of the same avail.
        # locally is equal to the number of the same avail.
        # in the database
        self.assertEqual(new_products.count(), count_avail)
        # Check that the returned products all have the same avail.
        for product in new_products:
            self.assertEqual(product.available, avail)

    def test_find_product_by_category(self):
        """It should find a product in the database by category"""
        # Create ten fake Products
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        # Get count of products with same category as first product
        categ = products[0].category
        count_categ = len([1 for product in products
                          if product.category == categ])
        # Find products by the same category in the database
        new_products = Product.find_by_category(categ)
        # Assert that the number of products of the same category
        # locally is equal to the number of the same category
        # in the database
        self.assertEqual(new_products.count(), count_categ)
        # Check that the returned products all have the same categ.
        for product in new_products:
            self.assertEqual(product.category, categ)

    def test_find_product_by_price(self):
        """It should find a product in the database by price"""
        # Create ten fake Products
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        # Get count of products with same price as first product
        price = products[0].price
        count_price = len([1 for product in products
                          if product.price == price])
        # Find products by the same price in the database
        new_products = Product.find_by_price(price)
        # Assert that the number of products of the same price
        # locally is equal to the number of the same price
        # in the database
        self.assertEqual(new_products.count(), count_price)
        # Check that the returned products all have the same price
        for product in new_products:
            self.assertEqual(product.price, price)

    def test_find_product_by_price_str(self):
        """It should find a product in the database via string price"""
        # Create fake Product and publish to database
        product = ProductFactory()
        product.create()
        # Find product by price (as a str value)
        products = Product.find_by_price(str(product.price))
        new_product = products[0]
        # Check that it matches the original product
        self.assertEqual(new_product.id, product.id)
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(new_product.price, product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_validation_error_on_update(self):
        """It should raise a validation error on update w/o id"""
        # Create fake Product
        product = ProductFactory()
        product.id = None
        product.create()
        # Check that the id was created
        self.assertIsNotNone(product.id)
        # Make id none
        product.id = None
        # Assert that a DataValidationError results from update
        self.assertRaises(DataValidationError, product.update)

    def test_validation_errors_on_deserialization(self):
        """It should raise validation errors when deserializing corrupt data"""
        # Create fake Product locally
        product = Product()
        # Check that an error results from calling deserialize
        # w/o a dict argument
        self.assertRaises(DataValidationError,
                          product.deserialize, 1)
        # Create a dict via serialization
        product_dict = ProductFactory().serialize()
        # Make available attribute invalid and check for error
        test_dict = product_dict
        test_dict["available"] = 1
        self.assertRaises(DataValidationError,
                          product.deserialize, test_dict)
        # Delete price attribute and check for error
        test_dict = product_dict
        del test_dict["price"]
        self.assertRaises(DataValidationError,
                          product.deserialize, test_dict)
