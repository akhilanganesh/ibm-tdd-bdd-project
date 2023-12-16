######################################################################
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
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from urllib.parse import quote_plus
from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_get_product(self):
        """It should read a Product from the database"""
        # Create 1 product in database
        test_product = self._create_products(1)[0]
        logging.debug("Test Product: %s", test_product.serialize())
        # Send a GET request to the product endpoint
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        # Check for 200
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        logging.info(response.json)
        # Check for matching json payload
        self.assertEqual(response.json, test_product.serialize())

    def test_get_nonexistent_product(self):
        """It should not read non-existent Product"""
        # Send a GET request to a non-existent product endpoint
        response = self.client.get(f"{BASE_URL}/321")
        # Check for 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product(self):
        """It should Update a Product in the database"""
        # Create a product fake
        product = ProductFactory()
        # Send POST request to base endpoint
        response = self.client.post(BASE_URL, json=product.serialize())
        logging.info(response.get_json())
        product.deserialize(response.get_json())
        # Check for 201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Now update the product and send PUT request, check for 200
        product.name = "NotInMyName"
        response = self.client.put(f"{BASE_URL}/{product.id}", json=product.serialize())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Send GET request and check for 200
        response = self.client.get(f"{BASE_URL}/{product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that response data has updated product data
        self.assertEqual(response.get_json(), product.serialize())

    def test_update_nonexistent_product(self):
        """It should not Update a nonexistent Product"""
        response = self.client.put(f"{BASE_URL}/321", json={})
        # Check for 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product_no_content_type(self):
        """It should not Update a Product with no Content-Type"""
        # Create a product fake
        product = ProductFactory()
        # Send POST request to base endpoint
        response = self.client.post(BASE_URL, json=product.serialize())
        logging.info(response.get_json())
        product.deserialize(response.get_json())
        # Check for 201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Now send bad data for update to product
        response = self.client.put(f"{BASE_URL}/{product.id}",
                                   data="bad data")
        # Check for 415
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_update_product_wrong_content_type(self):
        """It should not Update a Product with wrong Content-Type"""
        # Create a product fake
        product = ProductFactory()
        # Send POST request to base endpoint
        response = self.client.post(BASE_URL, json=product.serialize())
        logging.info(response.get_json())
        product.deserialize(response.get_json())
        # Check for 201
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Now send bad content type for update to product
        response = self.client.put(f"{BASE_URL}/{product.id}",
                                   data={}, content_type="plain/text")
        # Check for 415
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_delete_product(self):
        """It should Delete a Product in the database"""
        # Create 5 product fakes
        products = self._create_products(5)
        count = self.get_product_count()
        product = products[0]
        # Now send DELETE request, check for 204
        response = self.client.delete(f"{BASE_URL}/{product.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Send GET request and check for 404
        response = self.client.get(f"{BASE_URL}/{product.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Check for 1 less in total count
        new_count = self.get_product_count()
        self.assertEqual(new_count, count - 1)

    def test_delete_nonexistent_product(self):
        """It should not read non-existent Product"""
        # Send a DELETE request to a non-existent product endpoint
        response = self.client.delete(f"{BASE_URL}/321")
        # Check for 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_list_all_products(self):
        """It should list all Products in the database"""
        # Create 5 fake Products
        products = self._create_products(5)
        # Send GET request and check for 200
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that response data has 5 Products
        data = response.get_json()
        self.assertEqual(len(data), 5)
        # Check that response data matches local Products
        # in no particular order
        for product in products:
            self.assertIn(product.serialize(), data)

    def test_find_by_name(self):
        """It should find all products of a given name in the database"""
        # Create 5 fake Products
        products = self._create_products(5)
        # Get count of products with same name as first product
        name = products[0].name
        count_name = len([1 for product in products
                         if product.name == name])
        # Send GET request for query, check for 200
        response = self.client.get(BASE_URL, query_string=f"name={quote_plus(name)}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert that the number of products of the same name
        # locally is equal to the number of the same name
        # in the database
        data = response.get_json()
        self.assertEqual(len(data), count_name)
        # Check that the returned products all have the same name
        for entry in data:
            self.assertEqual(entry["name"], name)

    def test_find_by_category(self):
        """It should find all products of a given category in the database"""
        # Create 5 fake Products
        products = self._create_products(5)
        # Get count of products with same category as first product
        category = products[0].category
        count_category = len([1 for product in products
                             if product.category == category])
        # Send GET request for query, check for 200
        response = self.client.get(BASE_URL, query_string=f"category={quote_plus(category.name)}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert that the number of products of the same category
        # locally is equal to the number of the same category
        # in the database
        data = response.get_json()
        self.assertEqual(len(data), count_category)
        # Check that the returned products all have the same category
        for entry in data:
            self.assertEqual(entry["category"], category.name)

    def test_find_by_availability(self):
        """It should find all products of a given availability in the database"""
        # Create 5 fake Products
        products = self._create_products(5)
        # Get count of products with same availability as first product
        availability = products[0].available
        count_availability = len([1 for product in products
                                 if product.available == availability])
        # Send GET request for query, check for 200
        response = self.client.get(BASE_URL, query_string=f"available={quote_plus(str(availability))}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert that the number of products of the same availability
        # locally is equal to the number of the same availability
        # in the database
        data = response.get_json()
        self.assertEqual(len(data), count_availability)
        # Check that the returned products all have the same availability
        for entry in data:
            self.assertEqual(entry["available"], availability)

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
