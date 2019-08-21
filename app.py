from flask import Flask, request, jsonify
import json
from waitress import serve
from graphqlclient import GraphQLClient

# from flask_marshmallow import marshmalllow
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
PORT = 8080

graphqlClient = GraphQLClient("https://hasura-sa.cap.jaagalabs.com/v1/graphql")
graphqlClient.inject_token(
    "1SocialAlpha", 'x-hasura-admin-secret')

user_id = 12

problems = [
    {
        "title": "flask test 10",
        "description": "Sample article content",
        "user_id": 5,
        "max_population": 2323,
        "organization": "wewe"
    },
    {
        "title": "flask test 12",
        "description": "Sample article content",
        "user_id": 5,
        "max_population": 2323,
        "organization": "wewe"
    }
]

problems_update_query = '''
    {
    problems(where:{id:{_eq:%s}}){

     problem_owners{
      user_id
    }
    problem_watchers{
      user_id
    }
    problem_validations{
      user_id
    }
    problem_collaborators{
      user_id
    }


    }
    }
    ''' % user_id

problems_insert_query = '''
 {
    problems(where:{id:{_eq:%s}}){
         problems_tags{
        tag{
          users_tags{
            user_id
            tag_id
          }
        }
      }




    }
    }'''

# test = json.dumps(problems)
# print(test)


notifications_insert_mutation = '''
mutation insert_notifications($objects: [notifications_insert_input!]! ) {
    insert_notifications(
        objects:$objects
    ) {
        returning {
            id
            user_id
        }
    }
}
'''


test = [{"problem_id": 69, "user_id": 5, "tag_id": 4},
        {"problem_id": 69, "user_id": 5, "tag_id": 3}]
# .replace('$problems', json.dumps([{"title": "from flask api", "description": "ddasdasd", "max_population": 21, "user_id": 5}]))


@app.route("/")
def entry():
    # file = open("myfile.txt", "w+")
    # print(json.loads(graphqlClient.execute(query)))
    # print(mutation)
    # graphqlClient.execute(problems_insert_mutation)
    # graphqlClient.execute(problems_insert_mutation, {
    #                       'objects': list(problems)})

    # json_acceptable_string = payload.replace("'", "\"")

    # d = json.loads(json_acceptable_string)
    # print(d["data"]["problems"])
    # graphqlClient.execute(notifications_insert_mutation, {
    #     'objects': list(test)})

    # file.close()

    print("testing")
    return "working"


@app.route("/problems", methods=['POST'])
def handle_problem_event_trigger():
    # users_to_notify_on_insert = []
    users_to_notify_on_update = []
    problem_insert_notifications = []
    problem_update_notifications = []

    # print(request)
    # file = open("myfile.txt", "w+")
    # file.write(json.dumps(request.json))
    # file.close()
    # return json.dumps(request.json)
    print(request.json, "====request", type(request.json))

    trigger_payload = request.json
    print(trigger_payload, "notification payload",
          type(trigger_payload))
    problem_id = trigger_payload["event"]["data"]["new"]["id"]
    print("problem id==========", problem_id)
    user_id = trigger_payload["event"]["data"]["new"]["user_id"]

    if trigger_payload["event"]["op"] == "INSERT":
        problems_insert_query = '''
            {
              problems(where:{id:{_eq:%s}}){
               problems_tags{
                tag{
                 users_tags{
                  user_id
                  tag_id
                }
               }
              }
             }
            }''' % (problem_id)
        problem_insert_query_data = json.loads(graphqlClient.execute(problems_insert_query))[
            "data"]["problems"][0]
        for item, values in problem_insert_query_data.items():

            # print(item, "item", values)
            for tags in values:
                for tag in tags["tag"]["users_tags"]:
                    # print(tag, "tag")
                    problem_insert_notifications.append(
                        {"user_id": tag["user_id"], "tag_id": tag["tag_id"], "problem_id": problem_id})
        print("user to notify ========", problem_insert_notifications)
        try:
            graphqlClient.execute(notifications_insert_mutation, {
                'objects': list(problem_insert_notifications)})
        except:
            pass
    elif (trigger_payload["event"]["op"] == "UPDATE"):

        problems_update_query = '''
                        {
             problems(where:{id:{_eq:%s}}){

            problem_owners{
            user_id
            }
            problem_watchers{
            user_id
            }
            problem_validations{
            user_id
            }
            problem_collaborators{
            user_id
            }


            }
            }
        ''' % (problem_id)
        problem_update_query_data = json.loads(graphqlClient.execute(problems_update_query))[
            "data"]["problems"][0]
        for item, values in problem_update_query_data .items():
            for value in values:

                users_to_notify_on_update.append(value["user_id"])

        users_to_notify_on_update = list(set(users_to_notify_on_update))
        for user in users_to_notify_on_update:
            notifification_entry = {"user_id": user, "problem_id": problem_id}
            problem_update_notifications.append(notifification_entry)
        try:
            graphqlClient.execute(notifications_insert_mutation, {
                'objects': list(problem_update_notifications)})
        except:
            pass


if __name__ == "__main__":
    app.run(debug=True)
    # serve(app, listen='*:{}'.format(str(PORT)))
