from flask import Flask, request, jsonify
import json
from waitress import serve
from graphqlclient import GraphQLClient
import os


app = Flask(__name__)

PORT = 8080

graphqlClient = GraphQLClient(os.environ['HASURA_GRAPHQL_URL'])
graphqlClient.inject_token(
    os.environ['HASURA_GRAPHQL_ADMIN_SECRET'], 'x-hasura-admin-secret')



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


def get_problem_query(problem_id):
    problems_query = '''
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
    return problems_query


def get_solution_update_query(solution_id):

    solutions_query = '''
                        {
            solutions(where:{id:{_eq:%s}}){

            solution_owners{
            user_id
            }
            solution_watchers{
            user_id
            }
            solution_validations{
            user_id
            }
            solution_collaborators{
            user_id
            }


            }
            }
        ''' % (solution_id)
    return solutions_query


def get_enrichment_query(enrichment_id):
    enrichments_query = '''
                        {
            enrichments(where:{id:{_eq:%s}}){
            problem{


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
            }
        ''' % (enrichment_id)
    return enrichments_query


def add_owner(user_id, id, type):
    owner = []
    owner_insert_mutation = '''mutation insert_%s_owners($objects: [%s_owners_insert_input!]! ) {
    insert_%s_owners(
        objects:$objects
    ) {
        returning {
            
            user_id
        }
    }
}
''' % (type, type, type)
    owner_object = {"user_id": user_id, "{}_id".format(type): id}
    owner.append(owner_object)
    print(owner, "query==", owner_insert_mutation)
    try:
        graphqlClient.execute(owner_insert_mutation, {
            'objects': list(owner)})
    except:
        pass


def handle_notifications(trigger_payload, table, query, problem_id, user_id=None, notification_type=None):
    users_to_notify = []
    notifications = []
    # solution_id = None

    # if table == "solutions":
    #     solution_id = trigger_payload["event"]["data"]["new"]["id"]

    query_data = json.loads(graphqlClient.execute(query))[
        "data"][table][0]
    for item, values in query_data.items():
        for value in values:
            users_to_notify.append(value["user_id"])
    users_to_notify = set(users_to_notify)
    if user_id in users_to_notify:
        users_to_notify.remove(user_id)

    for user in users_to_notify:
        notifification_entry = {"user_id": user, "problem_id": problem_id}
        if user_id and notification_type:
            notifification_entry[notification_type] = user_id
        # if solution_id:
        #     notifification_entry["solution_id"] = solution_id
        notifications.append(notifification_entry)
    print(notifications, "=====notifications")
    try:
        graphqlClient.execute(notifications_insert_mutation, {
            'objects': list(notifications)})
    except:
        pass


def handle_solution_notifications(trigger_payload, table, query, solution_id, user_id=None, notification_type=None):
    users_to_notify = []
    notifications = []
    query_data = json.loads(graphqlClient.execute(query))[
        "data"][table][0]
    for item, values in query_data.items():
        for value in values:
            users_to_notify.append(value["user_id"])
    users_to_notify = set(users_to_notify)
    if user_id in users_to_notify:
        users_to_notify.remove(user_id)

    for user in users_to_notify:
        notifification_entry = {"user_id": user, "solution_id": solution_id}
        if user_id and notification_type:
            notifification_entry[notification_type] = user_id
        else:
            notifification_entry["is_update"] = True
        # if solution_id:
        #     notifification_entry["solution_id"] = solution_id
        notifications.append(notifification_entry)
    print(notifications, "=====notifications")
    try:
        graphqlClient.execute(notifications_insert_mutation, {
            'objects': list(notifications)})
    except:
        pass
    # return "working"


def handle_enrichments_notification(trigger_payload, query, enrichment_id, user_id):
    users_to_notify = []
    notifications = []
    problem_id = trigger_payload["event"]["data"]["new"]["problem_id"]
    query_data = json.loads(graphqlClient.execute(query))[
        "data"]["enrichments"][0]
    for item, users in query_data["problem"].items():
        for user in users:
            users_to_notify.append(user["user_id"])
    users_to_notify = set(users_to_notify)
    if user_id in users_to_notify:
        users_to_notify.remove(user_id)
    for user in users_to_notify:
        notifification_entry = {
            "user_id": user, "problem_id": problem_id, "enrichment_id": enrichment_id}

        notifications.append(notifification_entry)
    print(notifications, "=====notifications")
    try:
        graphqlClient.execute(notifications_insert_mutation, {
            'objects': list(notifications)})
    except:
        pass


@app.route("/")
def entry():

    print("testing")
    return "working"


@app.route("/problems/insert", methods=['POST'])
def handle_problem_insert():

    problem_insert_notifications = []

    trigger_payload = request.json

    problem_id = trigger_payload["event"]["data"]["new"]["id"]

    user_id = trigger_payload["event"]["data"]["new"]["user_id"]

    add_owner(user_id,problem_id,"problem")

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

        for tags in values:

            for tag in tags["tag"]["users_tags"]:

                if(tag["user_id"] != user_id):

                    problem_insert_notifications.append(
                        {"user_id": tag["user_id"], "tag_id": tag["tag_id"], "problem_id": problem_id})
        print("user to notify ========", problem_insert_notifications)
    try:
        graphqlClient.execute(notifications_insert_mutation, {
            'objects': list(problem_insert_notifications)})
    except:
        pass

    return "working"


@app.route("/problems/update", methods=['POST'])
def handle_problem_update():
    trigger_payload = request.json
    problem_id = trigger_payload["event"]["data"]["new"]["id"]
    user_id=trigger_payload["event"]["data"]["new"]["user_id"]

    if (trigger_payload["event"]["op"] == "UPDATE" and not trigger_payload["event"]["data"]["new"]["is_draft"]):

        query = get_problem_query(problem_id)
        handle_notifications(trigger_payload, "problems",
                             query, problem_id,user_id)

    return "working"


@app.route("/problems/collaboration", methods=['POST'])
def handle_problem_collaboration():

    trigger_payload = request.json
    problem_id = trigger_payload["event"]["data"]["new"]["problem_id"]
    user_id = trigger_payload["event"]["data"]["new"]["user_id"]
    query = get_problem_query(problem_id)

    handle_notifications(trigger_payload, "problems",
                         query, problem_id, user_id, "collaborator")
    return "working"


@app.route("/problems/validation", methods=['POST'])
def handle_problem_validation():

    trigger_payload = request.json
    problem_id = trigger_payload["event"]["data"]["new"]["problem_id"]
    user_id = trigger_payload["event"]["data"]["new"]["user_id"]
    query = get_problem_query(problem_id)

    handle_notifications(trigger_payload, "problems",
                         query, problem_id, user_id, "validated_by")
    return "working"


@app.route("/enrichments/insert", methods=['POST'])
def handle_enrichment_insert():
    trigger_payload = request.json
    enrichment_id = trigger_payload["event"]["data"]["new"]["id"]
    user_id = trigger_payload["event"]["data"]["new"]["user_id"]
    query = get_enrichment_query(enrichment_id)
    handle_enrichments_notification(
        trigger_payload, query, enrichment_id, user_id)
    return "working"


@app.route("/discussion_mentions", methods=['POST'])
def handle_discussion_mentions():
    trigger_payload = request.json
    user_to_be_notified = trigger_payload["event"]["data"]["new"]["user_id"]
    discussion_id = trigger_payload["event"]["data"]["new"]["discussion_id"]
    query = '''{
           discussion_mentions(where:{discussion_id:{_eq:%s}}){
            discussion{
              id
              problem{
                id
              }
            }
          }
            }''' % (discussion_id)
    problem_id = json.loads(graphqlClient.execute(query))[
        "data"]["discussion_mentions"][0]["discussion"]["problem"]["id"]
    notification = []
    notification_object = {"user_id": user_to_be_notified,
                           "problem_id": problem_id, "discussion_id": discussion_id}
    notification.append(notification_object)
    print("notification", notification)
    try:
        graphqlClient.execute(notifications_insert_mutation, {
            'objects': list(notification)})
    except:
        pass
    return "working"


@app.route("/solutions/insert", methods=['POST'])
def handle_solution_insert():
    users_to_notify = {}
    notifications = []
    trigger_payload = request.json
    solution_id = trigger_payload["event"]["data"]["new"]["id"]
    user_id = trigger_payload["event"]["data"]["new"]["user_id"]

    add_owner(user_id,solution_id,"solution")


    solution_insert_query = '''query{
    solutions(where:{id:{_eq:%s}}){


      problems_solutions{
        problem{
          problem_owners{
            user_id
            problem_id

          }
          problem_watchers{

            user_id
            problem_id

          }
          problem_validations{

            user_id
            problem_id

          }
          problem_collaborators{
            problem_id
            user_id

          }
        }
      }

    }

  }''' % (solution_id)
    query_data = json.loads(graphqlClient.execute(solution_insert_query))[
        "data"]["solutions"][0]["problems_solutions"]

    for problems in query_data:

        for item, users in problems["problem"].items():

            for user in users:

                if bool(user):
                    print(user)

                    users_to_notify["{}".format(str(user["user_id"]) + "-" +
                                                str(user["problem_id"]))] = user

    print("users to notify=====", users_to_notify)

    for items, user in users_to_notify.items():

        if user["user_id"] == user_id:
            del user
    for item, user in users_to_notify.items():
        notifification_entry = {
            "user_id": user["user_id"], "problem_id": user["problem_id"], "solution_id": solution_id}

        notifications.append(notifification_entry)
    print(notifications, "=====notifications")
    try:
        graphqlClient.execute(notifications_insert_mutation, {
            'objects': list(notifications)})
    except:
        pass
    return "working"


@app.route("/solutions/update", methods=['POST'])
def handle_solutions_update():
    trigger_payload = request.json
    solution_id = trigger_payload["event"]["data"]["new"]["id"]

    if (trigger_payload["event"]["op"] == "UPDATE" and not trigger_payload["event"]["data"]["new"]["is_draft"]):

        query = get_solution_update_query(solution_id)
        handle_solution_notifications(trigger_payload, "solutions",
                                      query, solution_id)

    return "working"


@app.route("/solutions/collaboration", methods=['POST'])
def handle_solution_collaboration():

    trigger_payload = request.json
    solution_id = trigger_payload["event"]["data"]["new"]["solution_id"]
    user_id = trigger_payload["event"]["data"]["new"]["user_id"]
    query = get_solution_update_query(solution_id)

    handle_solution_notifications(trigger_payload, "solutions",
                                  query, solution_id, user_id, "collaborator")
    return "working"


@app.route("/solutions/validation", methods=['POST'])
def handle_solution_validation():

    trigger_payload = request.json
    solution_id = trigger_payload["event"]["data"]["new"]["solution_id"]
    user_id = trigger_payload["event"]["data"]["new"]["user_id"]
    query = get_solution_update_query(solution_id)

    handle_solution_notifications(trigger_payload, "solutions",
                                  query, solution_id, user_id, "validated_by")
    return "working"


if __name__ == "__main__":
    # app.run(debug=True)
    serve(app, listen='*:{}'.format(str(PORT)))
