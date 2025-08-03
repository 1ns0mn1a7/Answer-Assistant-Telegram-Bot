import json
import os
from environs import Env
from google.cloud import dialogflow_v2 as dialogflow


def create_intent(project_id, display_name, training_phrases_parts, message_texts):
    intents_client = dialogflow.IntentsClient()
    parent = dialogflow.AgentsClient.agent_path(project_id)

    training_phrases = []
    for phrase in training_phrases_parts:
        part = dialogflow.Intent.TrainingPhrase.Part(text=phrase)
        training_phrases.append(dialogflow.Intent.TrainingPhrase(parts=[part]))

    text = dialogflow.Intent.Message.Text(text=message_texts)
    message = dialogflow.Intent.Message(text=text)

    intent = dialogflow.Intent(
        display_name=display_name,
        training_phrases=training_phrases,
        messages=[message]
    )

    response = intents_client.create_intent(request={"parent": parent, "intent": intent})
    print(f"Intent создан: {response.name} ({display_name})")


if __name__ == "__main__":
    env = Env()
    env.read_env()

    project_id = env.str("PROJECT_ID")
    google_credentials = env.str("GOOGLE_APPLICATION_CREDENTIALS")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credentials

    with open("questions.json", "r", encoding="utf-8") as f:
        intents_from_file = json.load(f)

    for intent_name, intent_content in intents_from_file.items():
        questions = intent_content["questions"]
        answer = intent_content["answer"]
        create_intent(project_id, intent_name, questions, [answer])
