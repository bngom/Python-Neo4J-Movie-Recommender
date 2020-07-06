from py2neo import Graph, Node
from passlib.hash import bcrypt
from datetime import datetime
import os
import pandas as pd
from flask_paginate import Pagination
from flask import request


url = os.environ.get('GRAPHENEDB_URL', 'http://localhost:7474')
#username = 'Graph'
#password = 'passer'
username = os.getenv('NEO4J_USERNAME')
password = os.getenv('NEO4J_PASSWORD')

graph = Graph(url + '/db/data/', username=username, password=password)
class User:
    def __init__(self, username):
        self.username = username

    def find(self):
        """Find if a user exists in Neo4j
        :return
            - return the username if the user exists
            - return None if the user does not exists"""
        result = graph.run("MATCH (a:User {name:$user}) RETURN a.name, a.password", user=self.username)
        if result is not None:
            print("result is not none")
            for item in result:
                return item['a.name'], item['a.password']
        else:
            return None, None

    def register(self, password):
        """Register a user in the application
        :argument
            - password: user defined password
        :returns
            - return True if succeed
            - return false if failure"""

        if not self.find():
            user = Node("User", name=self.username, password=bcrypt.encrypt(password))
            graph.create(user)
            return True
        else:
            return False

    def verify_password(self, password):
        """Verify password on login
        :argument
            - password: user typed password
        :returns
            - return True if succeeded
            - return false if failed"""
        try:
            user, pwd = self.find()
        except TypeError as e:
            user = None

        if user is not None:
            return bcrypt.verify(password, pwd)
        else:
            return False

    def like_movie(self, movieid):
        """Generate a relation (user)-[:LIKED]->(movie)"""

        query = '''MATCH (u:User {name:$user})
                   MATCH (m:Movie {movieId:$movieId})
                   MERGE (u)-[:LIKED]->(m)'''

        return graph.run(query, user=self.username, movieId=movieid)

    def get_liked_movies(self):
        """ Get the movies liked by the connected user
        :return
            - A record of movies liked by the connected user"""
        query = '''
        MATCH (u:User {name:$username})-[:LIKED]->(m:Movie)
        RETURN u.name, m.movieId, m.name'''

        return graph.run(query, username=self.username)

    def get_recommendation(self):
        """ Recommend movies to the user. This is based on the category of the movies liked by the user

        :return:
            - A record of movie
        """
        query = '''MATCH (u:User {name:$username})-[:LIKED]->(movies)-[:IS_CATEGORY]->(:Category)<-[:IS_CATEGORY]
                    -(movies2)-[:RELEASED_COUNTRY]->(:Country {name:'USA'})
                WHERE NOT (u)-[:LIKED]->(movies2) 
                AND 1990 <= movies2.released < 2000  
                WITH  DISTINCT movies2.name AS mo, movies2.released AS year, 
                 movies2.avg_vote as vote, movies2.genre as genre, movies2.actors as actors
                RETURN  mo, year, vote, genre, actors  ORDER BY vote DESC LIMIT 20'''

        return graph.run(query, username=self.username)


def timestamp():
    epoch = datetime.utcfromtimestamp(0)
    now = datetime.now()
    delta = now - epoch
    return delta.total_seconds()


def date():
    return datetime.now().strftime('%Y-%m-%d')


def get_css_framework():
    return 'bootstrap4'


def get_link_size():
    return 'sm'


def show_single_page_or_not():
    return False


def get_page_items():
    page = int(request.args.get('page', 1))
    per_page = request.args.get('per_page')
    if not per_page:
        per_page = 20
    else:
        per_page = int(per_page)
    offset = (page - 1) * per_page
    return page, per_page, offset


def get_pagination(**kwargs):
    kwargs.setdefault('record_name', 'movies')
    return Pagination(css_framework=get_css_framework(),
                      link_size=get_link_size(),
                      show_single_page=show_single_page_or_not(),
                      **kwargs
                      )


#get 90's us movies
def get_movies(skip, per_page):
    """ Get a record of US movies from 90's and the number of line in the record
    :param skip: Skip results at the top to limit the number of results.
    :param per_page: The number of movie displayed per page
    :return: A tuple with a record of movies and the number of element in the record
    """
    query = '''
          MATCH (m:Movie)-[:RELEASED_COUNTRY]->(c:Country {name:'USA'}), (m)<-[:ACTED_IN]-(actors)
          WHERE 1990 <= m.released < 2000
          WITH REDUCE(mergedString = "",word IN m.actors | mergedString+word+',') as actors, m 
          RETURN DISTINCT m, LEFT(actors,SIZE(actors)-1) as actors
          ORDER BY m.avg_vote DESC
          SKIP $skip
          LIMIT $per_page
          '''

    query2 = '''
          MATCH (m:Movie)-[:RELEASED_COUNTRY]->(c:Country {name:'USA'}), (m)<-[:ACTED_IN]-(actors)
          WHERE 1990 <= m.released < 2000
          WITH REDUCE(mergedString = "",word IN m.actors | mergedString+word+',') as actors, m 
          RETURN DISTINCT m, LEFT(actors,SIZE(actors)-1) as actors
          ORDER BY m.avg_vote DESC
              '''
    results = graph.run(query, skip=skip, per_page=per_page)
    rec = graph.run(query2)  # Refactor with a deep copy of results
    rec = [record for record in rec.data()]
    rec_df = pd.DataFrame(rec)
    rec_lst = list(rec_df['m'])
    total = len(rec_lst)

    return results, total
