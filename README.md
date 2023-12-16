# TDD / BDD Final Project

Final Project for the Coursera course **Introduction to TDD/BDD**. By Akhilan Ganesh. 

This project is primarily in Python, with the use of tools like PyUnit, Flask (RESTful API), Selenium, Gherkin syntax, and Behave.

## Tasks

In this project I use Test Driven Development (TDD) and Behavior Driven Development (BDD) techniques to write TDD test cases, BDD scenarios, and code, updating the following files:

```bash
tests/factories.py
tests/test_models.py
tests/test_routes.py
service/models.py
service/routes.py
features/products.feature
features/steps/load_steps.py
features/steps/web_steps.py
```

I was given partial implementations in each of these files.

### Part 1: Unit Tests for Product model and RESTful API routes (TDD)

In the first part of the project I implemented unit tests with PyUnit. My approach was a standard test-driven development process
where I implemented tests based on the needed specification, and after designing each test case, I implemented the required
functionality to pass the test. Then I updated the tests to include more rigorous details and again confirmed if my model and
API implementation was correct. I aimed for a test coverage of 100% as much as reasonably possible.

### Part 2: User Testing with Behave and Selenium (BDD)

In the second part of the project I worked on behavior-driven development tests with the design of user stories and
scenarios to capture the required web client functionality. This was specified in Gherkin syntax. Then, I implemented
step implementations with Behave, by using the Selenium WebDriver to simulate user browsing on the target site. This meant
simulation of setting fields, clicking buttons, copying and pasting, etc. to enact the Behave scenarios. In this case, the
web client was already designed and fully functioning, so I just needed to confirm my tests' correctness both on its own merit
and whether or not the web client was able to fully pass the tests (as it should).
