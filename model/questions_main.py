import string
import pandas as pd
import numpy as np
import webbrowser
from model.utterances import *
from model.classifiers import get_emotion, fluency_score, get_sentence_score, get_sentence_score_neg, get_sentence_score_pos, empathy_score, get_humour_scores

def get_main_questions(decision_maker):

    QUESTIONS = {

        #################### MAIN SESSION ####################

        "ask_name": {
            "model_prompt": introduction,
            "choices": {
                "open_text": lambda user_id, db_session, curr_session, app: save_name(decision_maker, user_id)
            },
            "protocols": {"open_text": []},
        },

        "opening_prompt": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_opening_prompt(decision_maker, user_id),
            "choices": {
                "yes": "remind_review",
                "no": "recommend_review" 
            },
            "protocols": {
                "yes":[],
                "no": [],
                },
        },

        "remind_review": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_review_protocols(decision_maker, user_id),
            "choices": {
                "Continue": "sleep_reload",
                "I'm on my phone": "recommend_review_more_details",
                "I'd like to know more":"recommend_review_more_details",
            },
            "protocols": {
                "Continue": [],
                "I'm on my phone": [],
                "I'd like to know more": [],
            },
        }, 

        "sleep_reload": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_fall_asleep_reload(decision_maker, user_id),
            "choices": {
                "continue": decision_maker.determine_next_prompt_haha("constant_practice_haha", "constant_practice_no_haha"),
            },
            "protocols": {
                "continue": [],
            },
        },

        "constant_practice_haha": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_practice_protocols(decision_maker, user_id),
            "choices": {
                "Haha": "constant_practice_funny",
                "That wasn't funny": "constant_practice_not_funny"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": [],
            },
        },

        "constant_practice_no_haha": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_practice_protocols(decision_maker, user_id),
            "choices": {
                "continue": "get_started",
            },
            "protocols": {
                "continue": [],
            },
        },

        "recommend_review": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_protocols_recommend(decision_maker, user_id),
            "choices": {
                # check haha_count and return either constant_practice_no_haha or constant_practice_haha based on how hi count is
                "Continue": decision_maker.determine_next_prompt_haha("constant_practice_haha", "constant_practice_no_haha"),
                "I'm on my phone": "recommend_review_more_details",
                "I'd like to know more":"recommend_review_more_details",
            },
            "protocols": {
                "Continue": [],
                "I'm on my phone": [],
                "I'd like to know more": [],
            },
        }, 

        "recommend_review_more_details": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_detailed_protocols_note(decision_maker, user_id),
            "choices": {
                # check haha_count and return either constant_practice_no_haha or constant_practice_haha based on how hi count is
                "Open this in a new tab": lambda user_id, db_session, curr_session, app: open_link_in_new_tab(),
                "Continue": "sleep_reload",
            },
            "protocols": {
                "Open this in a new tab": [],
                "Continue": [],
            },
        },

        "link_opened_continue": {
            "model_prompt": "This link has opened in a new tab.",
            "choices": {
                # check haha_count and return either constant_practice_no_haha or constant_practice_haha based on how hi count is
                "continue": "sleep_reload",
            },
            "protocols": {
                "continue": []
            },
        }, 

        "constant_practice_funny": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "get_started",
            },
            "protocols": {
                "continue": [],
            },
        },

        "constant_practice_not_funny": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "get_started",
            },
            "protocols": {
                "continue": [],
            },
        },

        "get_started": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_humour_jargon_note(decision_maker, user_id),
            "choices": {
                "Let's start": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_prompt_haha("ask_emotion_haha", "ask_emotion_no_haha"),
            },
            "protocols": {
                "Let's start": []
            },
        }, 

        "ask_emotion_haha": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_feeling_ask(decision_maker, user_id),
            "choices": {
                "Haha": "funny_emotion",
                "That wasn't funny": "not_funny_emotion"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },
        #TODO check determine_next_prompt_start_session function nand use
        "funny_emotion": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond_cont_feeling_ask(decision_maker, user_id),
            "choices": {
                "open_text": lambda user_id, db_session, curr_session, app: determine_next_prompt_start_session(decision_maker, user_id, True)
            },
            "protocols": {"open_text": []},
        },

        "not_funny_emotion": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond_cont_feeling_ask(decision_maker, user_id),
            "choices": {
                "open_text": lambda user_id, db_session, curr_session, app: determine_next_prompt_start_session(decision_maker, user_id, True)
            },
            "protocols": {"open_text": []},
        },

        "ask_emotion_no_haha": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_feeling_ask(decision_maker, user_id), 
            "choices": {
                "open_text": lambda user_id, db_session, curr_session, app: determine_next_prompt_start_session(decision_maker, user_id, False)
            },
            "protocols": {"open_text": []},
        },

        "guess_emotion": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_guess_emotion(decision_maker, user_id),
            "choices": {
                "That's correct": {
                    "Sad": "after_classification_negative", # changed all from negative for initial rule-based implementation
                    "Angry": "after_classification_negative",
                    "Anxious/Scared": "after_classification_negative",
                    "Happy/Content": "after_classification_positive", # changed from positive for initial rule-based implementation
                },
                "That's incorrect": "check_emotion",
            },
            "protocols": {
                "That's correct": [],
                "That's incorrect": [],
                },
        },

        "check_emotion": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_check_emotion(decision_maker, user_id),
            "choices": {
                "Sad": lambda user_id, db_session, curr_session, app: get_sad_emotion(decision_maker, user_id),
                "Angry": lambda user_id, db_session, curr_session, app: get_angry_emotion(decision_maker, user_id),
                "Anxious/Scared": lambda user_id, db_session, curr_session, app: get_anxious_emotion(decision_maker, user_id),
                "Happy/Content": lambda user_id, db_session, curr_session, app: get_happy_emotion(decision_maker, user_id),
            },
            "protocols": {
                "Sad": [],
                "Angry": [],
                "Anxious/Scared" : [],
                "Happy/Content": []
            },
        },

        # start positive session 
        # conversation redirects to MAIN SESSION (POSITIVE)
        "after_classification_positive": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_start_exploring(decision_maker, user_id),
            "choices": {
                "continue": lambda user_id, db_session, curr_session, app: determine_first_positive_session(decision_maker, user_id),
            },
            "protocols": {
                "continue": [], 
            },
        },

        # start negative session
        # conversation redirects to MAIN SESSION (NEGATIVE)
        "after_classification_negative": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_opening_prompt_negative(decision_maker, user_id),
            "choices": {
                "yes": "underlying_reason_yes", 
                "no": "underlying_reason_no", 
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        # before ending conversation

        # main session covered all 12 protocols (in mini sessions)
        "covered_all_sessions": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_review_any_pos(decision_maker, user_id),
            "choices": {
                "Yes": "choose_any",
                "No (end session)": lambda user_id, db_session, curr_session, app: end_session(decision_maker, user_id)
            },
            "protocols": {
                "Yes": [],
                "No (end session)": []
            },
        },

        "review_any_session": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_review_any(decision_maker, user_id),
            "choices": {
                "Yes": "choose_any",
                "No (end session)": lambda user_id, db_session, curr_session, app: end_session(decision_maker, user_id)
            },
            "protocols": {
                "Yes": [],
                "No (end session)": []
            },
        },

        "choose_any": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_select_protocol(decision_maker, user_id),
            "choices": {
                # TODO - check haha count
                "Playful mode": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_prompt_haha("ask_playful_mode_haha", "ask_playful_mode_no_haha"),
                "Self-glory": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_prompt_haha("ask_self_glory_haha", "ask_self_glory_not_haha"),
                "Incongruity (self and or world)": "ask_incongruity",
                "Contrasting views": "ask_feel_pre_cv",
                "Our own laughter brand": "ask_laughter_brand",
                "Feigning laughter": "ask_feigning_laughter",
                "Self-laughter": "ask_recent_error",
                "Laughing at setbacks": "ask_setback",
                "Laughing at hardships": "ask_hardship",                    
            },
            "protocols": {
                "Playful mode": [],
                "Self-glory": [],
                "Incongruity (self and or world)": [],
                "Contrasting views": [],
                "Our own laughter brand": [],
                "Feigning laughter": [],
                "Self-laughter": [],
                "Laughing at setbacks": [],
                "Laughing at hardships": [], 
            },
        },

        #################### ENDING MAIN SESSION

        "final_feeling_check": {
            #TODO: only use variable once so don't need
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_conclusion_ask_feeling(decision_maker, user_id),
            "choices": {
                "Better": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_prompt_haha("ending_better_haha", "ending_better_no_haha"),
                "No change": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_prompt_haha("ending_neg_haha", "ending_neg_no_haha"),
                "Worse": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_prompt_haha("ending_neg_haha", "ending_neg_no_haha"),
            },
            "protocols": {
                "Better": [],
                "No change": [],
                "Worse": [],
            },
        },

        "ending_better_haha": {
            "model_prompt":lambda user_id, db_session, curr_session, app: get_model_prompt_pos_protocols_encourage_end(decision_maker, user_id),
            "choices": {
                "Haha": "funny_ending",
                "That wasn't funny": "not_funny_ending"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_ending": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "Goodbye": "ending_message",
                "I'd like to have another session": "another_session",
            },
            "protocols": {
                "Goodbye": [],
                "I'd like to have another session": [],
            },
        },

        "not_funny_ending": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "Goodbye": "ending_message",
                "I'd like to have another session": "another_session",
            },
            "protocols": {
                "Goodbye": [],
                "I'd like to have another session": [],
            },
        },

        "ending_better_no_haha": {
            "model_prompt":lambda user_id, db_session, curr_session, app: get_model_prompt_pos_protocols_encourage_end(decision_maker, user_id),
            "choices": {
                "Goodbye": "ending_message",
                "I'd like to have another session": "another_session",
            },
            "protocols": {
                "Goodbye": [],
                "I'd like to have another session": [],
            },
        },

        "ending_neg_haha": {
            "model_prompt":lambda user_id, db_session, curr_session, app: get_model_prompt_neg_protocols_encourage_end(decision_maker, user_id),
            "choices": {
                "Haha": "funny_ending",
                "That wasn't funny": "not_funny_ending"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "ending_neg_no_haha": {
            "model_prompt":lambda user_id, db_session, curr_session, app: get_model_prompt_neg_protocols_encourage_end(decision_maker, user_id),
            "choices": {
                "Goodbye": "ending_message",
                "I'd like to have another session": "another_session",
            },
            "protocols": {
                "Goodbye": [],
                "I'd like to have another session": [],
            },
        },

        "ending_session_initial_pos": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_practice_protocols_encourage_end(decision_maker, user_id),
            "choices": {
                "Goodbye": "ending_message",
                "I'd like to have another session": "another_session",
            },
            "protocols": {
                "Goodbye": [],
                "I'd like to have another session": [],
            },
        },

        "ending_message": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_goodbye(decision_maker, user_id),
            "choices": {},
            "protocols": {},
        },

        "another_session": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_restart_note(decision_maker, user_id),
            "choices": {},
            "protocols": {},
        },
    }

    return QUESTIONS

def save_name(decision_maker, user_id):
    try:
        user_response = decision_maker.user_choices[user_id]["choices_made"]["ask_name"]
    except:  # noqa
        user_response = ""
    decision_maker.users_names[user_id] = user_response
    #decision_maker.chosen_personas[user_id] = "Kai"
    #decision_maker.datasets[user_id] = decision_maker.kai
    return "opening_prompt"

#TODO: random choice amongst all intro prompts!!!!!
def get_introduction_prompt(decision_maker, user_id):
    data = decision_maker.dataset
    column = data[introduction].dropna()
    question = np.random.choice(column).split("*")
    return question

# add check for whether user is familiar with the humorous protocols
def get_opening_prompt(decision_maker, user_id):
    name = decision_maker.users_names[user_id] 
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    print("prev qs are: ", prev_qs)
    data = decision_maker.dataset
    column = data[greeting].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format(name).split("*")
    return question


def get_model_prompt_review_protocols(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[protocols_note_pos].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format("").split("*")
    return question

def get_model_prompt_fall_asleep_reload(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[fall_asleep_reload].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format("").split("*")
    return question

def get_model_prompt_practice_protocols(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[practice_protocols_encourage_start].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format('\u0336'.join("perfect") + '\u0336').split("*")
    return question

def get_model_prompt_protocols_recommend(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[protocols_recommend].dropna()
    my_string1 = decision_maker.get_best_sentence_new(column1, prev_qs, user_id)
    column2 = data[protocols_note].dropna()
    my_string2 = decision_maker.get_best_sentence_new(column2, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    my_string = "*".join([my_string1, my_string2])
    question = my_string.format().split("*")
    return question

def get_model_prompt_detailed_protocols_note(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[detailed_protocols_note].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format('http://humandevelopment.doc.ic.ac.uk/papers/Self-initiated_humorous_protocols-f.pdf').split("*")
    return question

def open_link_in_new_tab():
    webbrowser.open_new_tab('http://humandevelopment.doc.ic.ac.uk/papers/Self-initiated_humorous_protocols-f.pdf')
    return "link_opened_continue"

def get_model_prompt_funny_respond(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[funny_respond].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_not_funny_respond(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[not_funny_respond].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_humour_jargon_note(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[humour_jargon_note].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_feeling_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[feeling_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_funny_respond_cont_feeling_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[funny_respond].dropna()
    my_string1 = decision_maker.get_best_sentence_new(column1, prev_qs, user_id)
    column2 = data[cont_feeling_ask].dropna()
    my_string2 = decision_maker.get_best_sentence_new(column2, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    my_string = "*".join([my_string1, my_string2])
    question = my_string.format().split("*")
    return question

def get_model_prompt_not_funny_respond_cont_feeling_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[not_funny_respond].dropna()
    my_string1 = decision_maker.get_best_sentence_new(column1, prev_qs, user_id)
    column2 = data[cont_feeling_ask].dropna()
    my_string2 = decision_maker.get_best_sentence_new(column2, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    my_string = "*".join([my_string1, my_string2])
    question = my_string.format().split("*")
    return question

# TODO: previously determine_next_prompt_opening - get emotion at start of session
def determine_next_prompt_start_session(decision_maker, user_id, respond_to_joke):
    if respond_to_joke:
        user_response = decision_maker.user_choices[user_id]["choices_made"]["ask_emotion_haha"]
        if user_response == "Haha":
            user_response = decision_maker.user_choices[user_id]["choices_made"]["funny_emotion"]
        else:
            user_response = decision_maker.user_choices[user_id]["choices_made"]["not_funny_emotion"]
    else:
        user_response = decision_maker.user_choices[user_id]["choices_made"]["ask_emotion_no_haha"]
    print("user response: ", user_response)
    emotion = user_response.lower()
    if emotion == 'sad' or emotion == 'angry' or emotion == 'anxious' or emotion == 'happy':
        decision_maker.user_emotions[user_id] = string.capwords(user_response)
        if user_response.lower() == 'happy':
            #self.get_happy_emotion(user_id)
            decision_maker.user_states[user_id] = "Positive"
            decision_maker.user_states_initial[user_id] = "Positive"
            return "after_classification_positive"
        else:
            decision_maker.user_states[user_id] = "Negative"
            decision_maker.user_states_initial[user_id] = "Negative"
            return "after_classification_negative"

    emotion = get_emotion(user_response)
    #emotion = np.random.choice(["Happy", "Sad", "Angry", "Anxious"]) #random choice to be replaced with emotion classifier
    if emotion == 'fear':
        decision_maker.guess_emotion_predictions[user_id] = 'Anxious/Scared'
        decision_maker.user_emotions[user_id] = 'Anxious'
        decision_maker.user_states_initial[user_id] = 'Negative'
    elif emotion == 'sadness':
        decision_maker.guess_emotion_predictions[user_id] = 'Sad'
        decision_maker.user_emotions[user_id] = 'Sad'
        decision_maker.user_states_initial[user_id] = 'Negative'
    elif emotion == 'anger':
        decision_maker.guess_emotion_predictions[user_id] = 'Angry'
        decision_maker.user_emotions[user_id] = 'Angry'
        decision_maker.user_states_initial[user_id] = 'Negative'
    else:
        decision_maker.guess_emotion_predictions[user_id] = 'Happy/Content'
        decision_maker.user_emotions[user_id] = 'Happy'
        decision_maker.user_states_initial[user_id] = 'Positive'
    #self.guess_emotion_predictions[user_id] = emotion
    #self.user_emotions[user_id] = emotion
    decision_maker.user_states[user_id] = decision_maker.user_states_initial[user_id]
    print('prev qs are: ', decision_maker.recent_questions[user_id])
    return "guess_emotion"
    
def get_model_prompt_guess_emotion(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[emotion_guess].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format(decision_maker.guess_emotion_predictions[user_id].lower()).split("*")
    #TODO
    print('prev qs are: ', decision_maker.recent_questions[user_id])
    return question

def get_model_prompt_check_emotion(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[wrong_emotion_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    return decision_maker.split_sentence(my_string)

def get_sad_emotion(decision_maker, user_id):
    decision_maker.guess_emotion_predictions[user_id] = "Sad"
    decision_maker.user_emotions[user_id] = "Sad"
    decision_maker.user_states_initial[user_id] = "Negative"
    decision_maker.user_states[user_id] = "Negative"
    return "after_classification_negative"

def get_angry_emotion(decision_maker, user_id):
    decision_maker.guess_emotion_predictions[user_id] = "Angry"
    decision_maker.user_emotions[user_id] = "Angry"
    decision_maker.user_states_initial[user_id] = "Negative"
    decision_maker.user_states[user_id] = "Negative"
    return "after_classification_negative"

def get_anxious_emotion(decision_maker, user_id):
    decision_maker.guess_emotion_predictions[user_id] = "Anxious/Scared"
    decision_maker.user_emotions[user_id] = "Anxious"
    decision_maker.user_states_initial[user_id] = "Negative"
    decision_maker.user_states[user_id] = "Negative"
    return "after_classification_negative" 

def get_happy_emotion(decision_maker, user_id):
    decision_maker.guess_emotion_predictions[user_id] = "Happy/Content"
    decision_maker.user_emotions[user_id] = "Happy"
    decision_maker.user_states_initial[user_id] = "Positive"
    decision_maker.user_states[user_id] = "Positive"        
    return "after_classification_positive"

def get_model_prompt_start_exploring(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[feeling_pos_respond].dropna()
    column2 = data[start_exploring].dropna()
    my_string1 = decision_maker.get_best_sentence_new(column1, prev_qs, user_id)
    my_string2 = decision_maker.get_best_sentence_new(column2, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    question = "*".join([my_string1, my_string2]).format().split("*")
    return question

#TODO NOW - ADD TO PREVIOUS SESSIONS
def determine_first_positive_session(decision_maker, user_id):
    # TODO decide if want to start with haha always?
    # positive mini sessions
    playful_session = decision_maker.determine_next_prompt_haha("ask_playful_mode_haha", "ask_playful_mode_no_haha")
    positive_sessions = [playful_session, "ask_incongruity_and_cv", "ask_laughter_brand"]
    chosen_session = np.random.choice(positive_sessions)
    if chosen_session in decision_maker.MINI_SESSION_QUESTIONS:
        print("current_choice in self.MINI_SESSION_QUESTIONS")
        current_mini_session_title = decision_maker.QUESTION_TO_MINI_SESSION[chosen_session]
        decision_maker.user_mini_sessions[user_id] = current_mini_session_title
        if len(decision_maker.user_covered_sessions[user_id]) == 0:
            decision_maker.user_covered_sessions[user_id] = [current_mini_session_title]
        else:
            decision_maker.user_covered_sessions[user_id].append(current_mini_session_title) 
        print("THE COVERED SESSIONS ARE!!!!!: ", decision_maker.user_covered_sessions)
    else:
        current_mini_session_title = decision_maker.QUESTION_TO_MINI_SESSION["ask_incongruity"]
        decision_maker.user_mini_sessions[user_id] = current_mini_session_title
        if len(decision_maker.user_covered_sessions[user_id]) == 0:
            decision_maker.user_covered_sessions[user_id] = [current_mini_session_title]
        else:
            decision_maker.user_covered_sessions[user_id].append(current_mini_session_title) 

    return chosen_session

def get_opening_prompt_negative(decision_maker, user_id):
    # time.sleep(7) TODO: decide how long
    name = decision_maker.users_names[user_id]
    feeling = get_emotional_state(decision_maker.user_emotions[user_id])
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[feeling_neg_respond].dropna()
    column2 = data[identified_reason_ask].dropna()
    my_string1 = decision_maker.get_best_sentence_new(column1, prev_qs, user_id)
    my_string2 = decision_maker.get_best_sentence_new(column2, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    question = "*".join([my_string1, my_string2]).format(feeling, name).split("*")
    return question

def get_emotional_state(user_emotion):
    emotion = "feeling"
    if user_emotion == "Angry":
        emotion = "anger"
    elif user_emotion == "Anxious":
        emotion = "fear"
    elif user_emotion == "Sad":
        emotion = "sadness"
    return emotion

def get_model_prompt_review_any_pos(decision_maker, user_id):
    name = decision_maker.users_names[user_id]
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[review_any_pos].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format(name).split("*")
    return question

def get_model_prompt_review_any(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[review_any].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

# TODO: add a time delay?
def end_session(decision_maker, user_id):
    if decision_maker.user_states_initial[user_id] == "Negative":
        return "final_feeling_check"
    else:
        return "ending_session_initial_pos"

def get_model_prompt_select_protocol(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[select_protocol].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_conclusion_ask_feeling(decision_maker, user_id):
    name = decision_maker.users_names[user_id]
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[conclusion_note].dropna()
    column2 = data[current_feeling_ask].dropna()
    my_string1 = decision_maker.get_best_sentence_new(column1, prev_qs, user_id)
    my_string2 = decision_maker.get_best_sentence_new(column2, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    question = "*".join([my_string1, my_string2]).format(name).split("*")
    return question

def get_model_prompt_pos_protocols_encourage_end(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[pos_respond].dropna()
    column2 = data[practice_protocols_encourage_end].dropna()
    my_string1 = decision_maker.get_best_sentence_new(column1, prev_qs, user_id)
    my_string2 = decision_maker.get_best_sentence_new(column2, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    question = "*".join([my_string1, my_string2]).format().split("*")
    return question

def get_model_prompt_neg_protocols_encourage_end(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[neg_respond].dropna()
    column2 = data[practice_protocols_encourage_end].dropna()
    my_string1 = decision_maker.get_best_sentence_new(column1, prev_qs, user_id)
    my_string2 = decision_maker.get_best_sentence_new(column2, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    question = "*".join([my_string1, my_string2]).format().split("*")
    return question

def get_model_prompt_practice_protocols_encourage_end(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[practice_protocols_encourage_end].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_goodbye(decision_maker, user_id):
    name = decision_maker.users_names[user_id]
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[goodbye].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format(name).split("*")
    return question

def get_model_prompt_restart_note(decision_maker, user_id):
    name = decision_maker.users_names[user_id]
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[restart_note].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format(name).split("*")
    return question
    