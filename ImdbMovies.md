# **Imdb movies analysis with Neo4j**
DSTI DE S20


*   Barthelemy Diomaye NGOM
*   Saifuddin Mohammad

https://github.com/bngom/Movie-Recommender-Engine.git

  

## **Project description**

**IMDb** is the world's most popular and authoritative source for movie, TV and celebrity content. The objective of this study is to explore datasets from IMDb using **Neo4j** in order to get insights from the Data. We will then buil a [movie recommender](https://github.com/bngom/Movie-Recommender-Engine.git) application with **python** based on movies that people liked.


The dataset we work on is `IMDb movies extensive dataset` found at: *https://www.kaggle.com/stefanoleone992/imdb-extensive-dataset*

To get insights we are going to import, model, preprocess the data. We will use powerfull technics that Neo4j provides us to leverage data and relationship between data.

## **Model creation**

In the following section we are going to process our data in order to create a model. Neo4j offers a powerfull syntax that allow us to perform complex queries with  few lines of code. The code to create Node and relation creation are in some part in this study nested. We will explain for each part what the query perfoms in detail.


#### **Memory Management**

> In the following section we assume that you  created a database in *Neo4j desktop* and apply recommanded parameter on your setting file. To get recommanded parameter :
1.   Open the *Neo4j desktop terminal*
2.   go to bin folder:**cd bin**
3.   type: **neo4j-admin memrec**
4.   Apply the memory settings recommended
 
![alt text](https://drive.google.com/uc?export=view&id=1dJPWVQ6yWSYUvfpwz5_4x4AKgO8tOfNK)

#### **The datasets**


The data are contained in four files - `IMDb-movies.csv`, `IMDb-names.csv`, `IMDb-ratings.csv` and `IMDb-title_principals.csv`.

**IMDb-movies.csv:**

> *This file contains information regarding the title, language, country, duration, votes and reviews. Another important column is 'imdb_title_id' this is a common column in other files and can be used as a key.*

**IMDb-names.csv:**

> *This file contains information on the actor/actress names and also date/place of birth and deaths. There is an column 'imdb_name_id' - just like the movies file this column can be used a key to traverse through the entire dataset.*

**IMDb-ratings.csv:**

> *This file contains a range of ratings: avgerage votes, 1 to 10 ratings, number of ratings and their medians, we also have ratings based on gender and age groups. These ratings corresponding to a single column 'imdb_title_id' which can be used to map the movies dataset. *

**IMDb-title_principals.csv:**

> *This file contains the role of each person(actor, director, producer) corresponding to each movie. This is categorized using the 'imdb_title_id' and 'imdb_name_id' from the other files. These keys are used to map through out the dataset.*

#### **Constraints and indexes**
In this section we will create unique property constraints and indexes for faster processing of queries. 
Unique property constraints ensure that property values are unique for all nodes with a specific label.


```
CREATE CONSTRAINT ON (p:Person) ASSERT p.p_id IS UNIQUE;
CREATE CONSTRAINT ON (m:Movie) ASSERT m.movieId IS UNIQUE;
CREATE CONSTRAINT ON (c:Category) ASSERT c.name IS UNIQUE;
CREATE CONSTRAINT ON (l:Language) ASSERT l.name IS UNIQUE;
CREATE CONSTRAINT ON (co:Country) ASSERT co.name IS UNIQUE;
CREATE INDEX FOR (m:Movie) ON (m.category);
CREATE INDEX FOR (m:Movie) ON (m.language);
CREATE INDEX FOR (m:Movie) ON (m.country);
#CREATE INDEX FOR (m:Movie) ON (m.avg_vote);
#CREATE INDEX FOR (c:Category) ON (c.avg_vote);
```

#### **Loading the dataset**
In this section we start to load data in the database with `IMDB-movies.csv` file.

We create a node with label `Movie` and give it several properties using reference variables for each column that we intend to use. For columns we want to use as `numeric` we use the `toInteger()` function to cast values as by default everything in neo4j is a string. 

The `:auto` command will send the Cypher query following it, in an auto committing transaction. We use `PERIODIC COMMIT` to instruct Neo4j to perform a commit after a number of rows. This reduces the memory overhead of the transaction state.

> The original name of the dataset is `IMDb names.csv` we renamed it as `IMDb-movies.csv`


```
:auto USING PERIODIC COMMIT 
LOAD CSV WITH HEADERS FROM 'file:///IMDb-movies.csv' AS movies FIELDTERMINATOR ','
CREATE (m:Movie {name:movies.title, movieId:movies.imdb_title_id, language:movies.language, country:movies.country, 
        released:toInteger(movies.year), duration:toInteger(movies.duration), avg_vote:toFloat(movies.avg_vote), genre:trim(movies.genre)})
```

As we explore the dataset, we observe that the columns `genre` , `language` and `country` are more beneficial as a node than a property. 

From Movie node, we generate three new nodes based on the Category, Language and Country. The challenge here is that these properties are sometime constitued by multiple elements. 

For each property, we first update the property by transforming it as a list of elements, then based on the Movie we MATCH or CREATE a new node and the corresponding relation.


```
#Make the split using ',' 

MATCH (mo:Movie)
SET mo.category = split(mo.genre, ",")
SET mo.language = split(mo.language, ",")
SET mo.country = split(mo.country, ",")

#MERGE or CREATE the node and the Relation for above columns: 
# The below queries are slow as each one checks - if the relation already exists and creates a new one if it doesn't already exist.
# This avoids duplication
MATCH (mo:Movie)
FOREACH(value IN mo.category |
	MERGE (c:Category {name:value})
	MERGE (mo)-[:IS_CATEGORY]->(c) )

MATCH (mo:Movie)
FOREACH(value IN mo.language |
	MERGE (l:Language {name:value})
	MERGE (mo)-[:AVAILABLE_LANGUAGE]->(l) ) 


MATCH (mo:Movie)
FOREACH(value IN mo.country |
	MERGE (co:Country {name:value})
	MERGE (mo)-[:RELEASED_COUNTRY]->(co))
```

Now, we load another file **`IMDB-names.csv`** from the dataset.
This file contains actor/actress names, their birthdate and other information we would use further.

One interesting column is `imdb_name_id` - this is a key to traverse through different files using a common id. 

We create another node with label `Person` 

> `IMDB names.csv` is the name of the file when you download it. It is renamed to `IMDB-names.csv`


```
LOAD CSV WITH HEADERS FROM 'file:///IMDb-names.csv' AS n FIELDTERMINATOR ','	
CREATE(p:Person {name:n.name, p_id:n.imdb_name_id, birth_year:toInteger(n.birth_year)})
```

The `IMDb-title_principals.csv` file do the link between the Movies and the Person(actors, actress,  directors, producers, writers...). 
In the following query for each Person we match the corresponding lines in the `IMDb-title_principals.csv`. Then depending on the category(actor, director, ...) we create a relation based on this pattern `(Person)-[:RELATION]->(Movie)`




```
LOAD CSV WITH HEADERS FROM 'file:///IMDb-title_principals.csv' AS t FIELDTERMINATOR ','
CREATE (x:Title {movie_id:t.imdb_title_id, personnage:t.imdb_name_id, category:t.category })

#ACTEDIN actor
MATCH (x:Title {category:"actor"})
MATCH (mo:Movie {movieId:x.movie_id})
MATCH (p:Person {p_id:x.personnage}) 
MERGE (p)-[:ACTED_IN]->(mo)

#ACTEDIN actress
MATCH (x:Title {category:"actress"})
MATCH (mo:Movie {movieId:x.movie_id})
MATCH (p:Person {p_id:x.personnage}) 
MERGE (p)-[:ACTED_IN]->(mo)

#PRODUCED
MATCH (x:Title {category:"producer"})
MATCH (mo:Movie {movieId:x.movie_id})
MATCH (p:Person {p_id:x.personnage}) 
MERGE (p)-[:PRODUCED]->(mo)

#DIRECTED
MATCH (x:Title {category:"director"})
MATCH (mo:Movie {movieId:x.movie_id})
MATCH (p:Person {p_id:x.personnage}) 
MERGE (p)-[:DIRECTED]->(mo)

#WROTE
MATCH (x:Title {category:"writer"})
MATCH (mo:Movie {movieId:x.movie_id})
MATCH (p:Person {p_id:x.personnage}) 
MERGE (p)-[:WROTE]->(mo)
```

![alt text](https://drive.google.com/uc?export=view&id=1gibaYincOm05ZDEztBuphZ6GeqULerPy) 

Now we load the file `IMDb-ratings.csv` and use the following as properties for our Movies

This file contains calculated information on ratings from different sources. We use the SET keyword to add each column as a property 


```
LOAD CSV WITH HEADERS FROM 'file:///IMDb-ratings.csv' AS r FIELDTERMINATOR ','
MATCH (m:Movie {movieId:r.imdb_title_id})
SET m.total_votes = toInteger(r.total_votes)
SET m.median_vote = toInteger(r.median_vote)   
SET m.votes_10 = toInteger(r.votes_10)  
SET m.votes_5 = toInteger(r.votes_5)  
SET m.votes_1 = toInteger(r.votes_1)
SET m.males_allages_votes = toInteger(r.males_allages_votes)
SET m.females_allages_votes = toInteger(r.females_allages_votes)
```


```
MATCH (n:Title) DETACH DELETE n 
```

Now we have 5 (nodes), 7 [:RELATIONS] and properties for each node.  

When we put everything together, and CALL db.schema.visualization :
We have the following graph.


```
CALL db.schema.visualization
```

![alt text](https://drive.google.com/uc?export=view&id=1Nl1i60SfW75IvxshT-vqeZxn_OOug0PS)

Now, we have the graph ready for queries with the following nodes, relations and properties created: 

![alt text](https://drive.google.com/uc?export=view&id=1FUkCFrVmqNvqvWCM-OCQhQJ52jHeUOF1)



A last operation for our model. Here we added the actors as a property in movie. This will be usefull for our python application.


```
MATCH (m:Movie)-[:RELEASED_COUNTRY]->(c:Country {name:'USA'}), (m)<-[:ACTED_IN]-(actors)
WHERE 1990 <= m.released < 2000
WITH  m, actors
FOREACH (_ IN actors.name |
  SET m.actors = coalesce(m.actors, []) + actors.name)
```

## **Performing queries on the graph** 




#### What is the worst rated movie in the "Toy Story" series?
Since there could be multiple titles with the name `Toy story` we use a regular expression to filter the titles. Then we use the `min()` function to calculate the minimum votes and hold this value in `min` variable using WITH keyword.

In the second MATCH we pass the intermediate `min` value as a property for Movie to return the least rated movie out of the series.


```
MATCH (m:Movie) 
WHERE m.name=~ 'Toy Story.*'
WITH min(m.avg_vote) as min
MATCH (n:Movie {avg_vote:min})
WHERE n.name =~ 'Toy Story.*'
RETURN n.name, n.avg_vote, n.total_votes
ORDER BY n.total_votes
```

Here, **Toy Story 4** and **Toy Story 2** has been rated worst compared to other titles in the series. They both have same average vote but `Toy story 4` has less number of vote.



![alt text](https://drive.google.com/uc?export=view&id=1CG8YGQ5yX87Wmq9Kg-I1VW6WJfuxIqrW)


### Behaviour of votes across genre.

For each movie we consider the total number of votes, the genre and the average votes.Then, we filter on genre which has more than **10.000 votes**.

For this query we used aggregation function such as `count` to have to total number of votes for each category and `avg`to have the average of rates given by user to each category.


```
MATCH (m)-[:IS_CATEGORY]->(c) 
WITH count(m.total_votes) AS Total_vote, trim(c.name) AS Category, avg(toFloat(m.avg_vote)) AS avg 
WHERE Total_vote >= 10000 
RETURN Total_vote,  Category, avg  ORDER BY Total_vote DESC
```


The category **Drama** has obviously more success. It received more votes and has the heighest average rate.


![alt text](https://drive.google.com/uc?export=view&id=1U9MzVb29tB2gOh0iGZH0_4YQyJK_XE9I)


### Which actors have worked for both **James Cameron** and **Chris Nolan**

Here we find the common actor for two directors. We filter person using the `[:DIRECTED]` and `[:ACTED_IN]` relation. Instead of doing MATCH twice for each director, we can do a nested query as follows: 


```
MATCH (Nolan:Person{name:'Christopher Nolan'}) - [:DIRECTED] -> (movies1) <- [:ACTED_IN]- (actors) ,
(actors)-[:ACTED_IN] ->(movies2)<-[:DIRECTED]-(James:Person{name:'James Cameron'}) 
RETURN actors, movies1, movies2, Nolan, James
```

From the graph we can see that only "**Leonardo DiCaprio**" has worked with both the directors in Movies : **Titanic** and **Inception**. 

![alt text](https://drive.google.com/uc?export=view&id=1ffavt0IjTtFWDR1AscBO3K8tn4Dul1V2) 

### Best combo: **Leo and Chris** or **Leo and James**? 

We will try to see wich combination has been more succesfull by returning the score (rating) for each movie

*The Winner is **Leonardo Dicaprio and Christopher Nolan** for the movie "**Inception**"* 




```
MATCH (:Person{name:'Christopher Nolan'}) - [:DIRECTED] -> (lc:Movie) <- [:ACTED_IN]- (:Person{name:'Leonardo DiCaprio'}) 
MATCH (:Person{name:'James Cameron'}) - [:DIRECTED]-> (lj:Movie) <-[:ACTED_IN] - (:Person{name:'Leonardo DiCaprio'})
RETURN lc.avg_vote AS Inception, lj.avg_vote AS Titanic
```

![alt text](https://drive.google.com/uc?export=view&id=1aRPkmCFLRZ4EE3HTIfgaZ1045ZpU1sV5) 

### Who ever have collaborated with **Leonardo DiCaprio**?


```
MATCH (p:Person {name:"Leonardo DiCaprio"})-[]->(m)<-[]-(p2)
RETURN p,p2,m
```

**137 Person** worked with DiCaprio in **19 movies**

![alt text](https://drive.google.com/uc?export=view&id=12Vyy__wPhh3h9Q-yPFqe1yFAy54TE3oc) 


### Performance of French movies in USA and Russia

Here, we compare the ratings of `French` Movies released in USA and Russia. We can do this using the properties from Movies node and relationship between movies and countries. 

We use the `avg()` function to return average of ratings. Since the relation is obvious here, we can use `[]` instead of specifiying the relation name - This highlights the convinience of Neo4J. 



```
MATCH (ru:Country{name:'Russia'}) <- [] - (mo:Movie) - [] -> (fr:Language{name:'French'}) <- [] -(m:Movie)- [] -> (usa:Country{name:'USA'})
RETURN avg(m.avg_vote) AS French_movies_released_in_USA, m.country,
       avg(mo.avg_vote) AS French_movies_released_in_Russia, mo.country
```

We can see **French** movies are more popular in **Russia** compared to **USA**.

![alt text](https://drive.google.com/uc?export=view&id=1cJBe6YAae983NgaL2ZqI6MyzJINdTisP) 

### Trend of votes by male and female based on duration of movies 

We study the behaviour of votes logged by males and females according to the movie duration of each genre. 

To make the contrast obvious we order the table according to duration of movie. 


```
MATCH (m:Movie)-[:IS_CATEGORY]->(c:Category) 
WITH trim(c.name) AS Category, toInteger(avg(m.duration)) AS Avg_duration,
	    toInteger(sum(m.males_allages_votes)) AS male_votes, toInteger(sum(m.females_allages_votes)) AS female_votes
RETURN Category, Avg_duration, male_votes, female_votes ORDER BY Avg_duration desc
```

![alt text](https://drive.google.com/uc?export=view&id=1zf4tDjo4xIGvP1BwDZ_q-BGWGSozZweT) 
