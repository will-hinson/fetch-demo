# Fetch Data Engineering Take-Home

## Introduction
This repository contains my submission for the Fetch data engineering take-home.

## Running locally
First, you'll need to clone this repository:

```shell
git clone https://github.com/will-hinson/fetch-data-engineering-demo.git
cd fetch-data-engineering-demo
```

By default, the entire application is configured to be run using `docker compose` and the configuration provided in `demo.env`. You may start all of the containers with the following commands:

```shell
docker compose build
docker compose up
```

The application will start in the `fetch-demo` container and it will log all output to the console. No knowledge of Python is required to start the application, a `Dockerfile` is provided in `src` that will handle setup and dependencies.

*Note that the containers are set up to perform initial healthchecks and the `fetch-demo` container may take up to 20 seconds to start after the Localstack container is ready.*

## Questions
**The following are my answers to the questions provided in the assignment:**

#### *1. How would you deploy this application in production?*
   - In its current state, the simplest way to deploy this application would be to use ECS.
   - Connection secrets could be passed in using the `environment` list in the `containerDefinitions`.
   - The Postgres instance could be created using RDS if it didn't already exist separately.
#### *2. What other components would you want to add to make this production ready?*
   - Before considering this application production ready, I would want to make the following improvements:
     - Integrate with Amazon CloudWatch to allow more robust monitoring of performance and logging of exceptions.
     - Set up more robust dependency injection for connection secrets.
     - Add error handling to re-establish both the SQS and SQL connections if they are dropped.
#### *3. How can this application scale with a growing dataset?*
  - This existing application could make use of threads to process more messages concurrently.
  - Instances of the application could be set up with load balancing to scale out as needed if the message queue started growing too large.
  - The Postgres database could be set up with EBS or made distributed via sharding to improve throughput.
  - A document database like DynamoDB could be used to store the records from the SQS queue and a warehousing process could insert them into the relational database later on.
#### *4. How can PII be recovered later on?*
   - The PII is masked using the AES-256 algorithm. Since this algorithm is symmetric, the PII can be decoded using AES-256 decryption and the encryption key provided in `demo.env`.
   - This decryption step could either occur directly in the Postgres database via the `pgp_sym_decrypt()` function or the data could be pulled into a Python data structure (e.g., a DataFrame) and decrypted using the `AesDecryptor` class in `fetch_demo.cipher`.
#### *5. What are the assumptions you made?*
  - The AES output for the two masked fields will never exceed 256 bytes in length. *The width of the columns in the table could be widened as necessary to accommodate changes in the future.*
  - The only valid compound key for the `user_logins` table includes all columns. *Adding an auto-increment primary key would eliminate this assumption.*
  - The `app_version` field will always be a triad and dot separators can simply be dropped since it needs to be stored as an integer. *If this isn't the case, versions 2.3.0 and 2.30 would clash.*

## Next Steps

- Write a client class and dataclasses to abstract reading objects from SQS. This would make our codebase less tightly integrated with SQS and make our `__main__.py` easier to maintain.
- Create a session manager class that could handle logging in a more robust manner and re-establish dropped connections.
- Implement more flexible configuration than using a `.env` file. *Ideally, YAML or JSON could be used for configuration.*
