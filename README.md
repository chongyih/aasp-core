# Automatic Assessment Platform (AASP)
This project is developed as part of my Final Year Project in Nanyang Technological University, Singapore.

## Instructions

### Local Development
1. Clone the repository, check out the `development` branch.
   ```bash
   # via http
   git clone https://github.com/leejunweisg/aasp
   
   # or via ssh (you need to add your ssh publickey to your github account)
   git clone git@github.com:leejunweisg/aasp.git
   ```

2. Make a copy of the `.env_dev` example file and save it as `.env`.
   ```shell
   cp ./config/.env_dev ./config/.env
   ```

3. Open `.env` and update the `SECRET_KEY` and `AASP_POSTGRES_PASSWORD` fields.

4. With docker-compose, create and start the containers:
   ```shell
   docker-compose -f docker-compose-dev.yml up -d
   ```
   
5. Open the project in your IDE, create a virtual environment and install the requirements.
   ```shell
   # unix/linux
   python3 -m venv venv
   source ./venv/bin/activate
   python3 -m pip install -r requirements.txt
   ```

6. Since this is the first launch, the database needs to be generated with Django, and pre-populated with required data.
   ```shell
   python3 manage.py gendb
   ```

7. Run the development webserver. The site will be accessible at `http://localhost:8000/`
   ```shell
   python3 manage.py runserver
   ```


### Production

#### Initial Deployment

1. Clone the repository, check out the `main` branch.
   ```bash
   # via http
   git clone https://github.com/leejunweisg/aasp
   
   # or via ssh (you need to add your ssh publickey to your github account)
   git clone git@github.com:leejunweisg/aasp.git
   ```

2. Make a copy of the `.env_prod` example file and save it as `.env`.
   ```shell
   cp ./config/.env_prod ./config/.env
   ```

3. Open `.env` and update the `SECRET_KEY` and `AASP_POSTGRES_PASSWORD` fields.

4. With docker-compose, create and start the containers:
   ```shell
   sudo docker-compose -f docker-compose.yml up -d
   ```

5. Since this is the first launch, the database needs to be generated with Django, and pre-populated with required data.
   ```shell
   # assuming 'aasp_aasp_web_1' is the name of the aasp_web container
   sudo docker exec -it aasp_aasp_web_1 python3 manage.py gendb
   ```

6. The site should now be accessible at `http://<docker-host-ip>/`

#### Update instructions
Note: If changes were made to the database schema, make sure to commit the migration files as well.

1. Push your commits to remote.
2. On the server, pull the new changes and recreate containers if necessary:
   ```shell
   git pull
   sudo docker-compose -f docker-compose.yml up -d
   ```

## Credits
### Contributions
- Lee Jun Wei ([LinkedIn](https://www.linkedin.com/in/leejunweisg/))

### Others
- Admin Dashboard Template from https://github.com/zuramai/mazer