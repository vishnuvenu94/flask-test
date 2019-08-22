from flask import Flask, request, jsonify
import json
from waitress import serve
from graphqlclient import GraphQLClient


app = Flask(__name__)

PORT = 8080

graphqlClient = GraphQLClient("https://hasura-sa.cap.jaagalabs.com/v1/graphql")
graphqlClient.inject_token(
    "1SocialAlpha", 'x-hasura-admin-secret')


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


def handle_notifications(trigger_payload, table, query, problem_id, user_id=0, notification_type=""):
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
        notifification_entry = {"user_id": user, "problem_id": problem_id}
        if user_id:
            notifification_entry[notification_type] = user_id
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

    # users_to_notify_on_update = []
    problem_insert_notifications = []
    # problem_update_notifications = []

    # print(request.json, "====request", type(request.json))

    trigger_payload = request.json
    # print(trigger_payload, "notification payload",
    #       type(trigger_payload))
    problem_id = trigger_payload["event"]["data"]["new"]["id"]
    # print("problem id==========", problem_id)
    user_id = trigger_payload["event"]["data"]["new"]["user_id"]

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
    # users_to_notify_on_update = []
    # problem_update_notifications = []
    trigger_payload = request.json
    problem_id = trigger_payload["event"]["data"]["new"]["id"]

    user_id = trigger_payload["event"]["data"]["new"]["user_id"]

    if (trigger_payload["event"]["op"] == "UPDATE" and not trigger_payload["event"]["data"]["new"]["is_draft"]):

        query = get_problem_query(problem_id)
        handle_notifications(trigger_payload, "problems",
                             query, problem_id)
        # print("====in")
        # problem_update_query_data = json.loads(graphqlClient.execute(problems_update_query))[
        #     "data"]["problems"][0]
        # for item, values in problem_update_query_data.items():
        #     for value in values:

        #         users_to_notify_on_update.append(value["user_id"])

        # users_to_notify_on_update = list(set(users_to_notify_on_update))
        # for user in users_to_notify_on_update:
        #     notifification_entry = {"user_id": user, "problem_id": problem_id}
        #     problem_update_notifications.append(notifification_entry)
        # print("users on update===", problem_update_notifications)
        # try:
        #     graphqlClient.execute(notifications_insert_mutation, {
        #         'objects': list(problem_update_notifications)})
        # except:
        #     pass
    return "working"


@app.route("/problems/collaboration", methods=['POST'])
def handle_problem_collaboration():

    trigger_payload = request.json
    problem_id = trigger_payload["event"]["data"]["new"]["problem_id"]
    user_id = trigger_payload["event"]["data"]["new"]["user_id"]
    query = get_problem_query(problem_id)

    handle_notifications(trigger_payload, "problems",
                         query, problem_id, user_id, "collaborator")


@app.route("/problems/validation", methods=['POST'])
def handle_problem_validation():

    trigger_payload = request.json
    problem_id = trigger_payload["event"]["data"]["new"]["problem_id"]
    user_id = trigger_payload["event"]["data"]["new"]["user_id"]
    query = get_problem_query(problem_id)

    handle_notifications(trigger_payload, "problems",
                         query, problem_id, user_id, "validated_by")


if __name__ == "__main__":
    app.run(debug=True)
    # serve(app, listen='*:{}'.format(str(PORT)))
