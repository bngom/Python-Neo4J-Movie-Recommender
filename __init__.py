from .models import graph

graph.schema.create_uniqueness_constraint("User", "username")


