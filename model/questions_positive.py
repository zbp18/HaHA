from model.utterances import *
from model.questions_main import *
from model.questions_mini_session import *
from model.questions_negative import *
from model.questions_reused import *

def get_positive_questions(decision_maker):

    #################### MAIN SESSION (POSITIVE) ####################

    QUESTIONS = {
        
        # random choice between 3 specific mini sessions: 
        # 1) playful mode and self-glory: 
        # "ask_playful_mode" (see above)

        # 2) incongruity and contrasting views:
        "ask_incongruity_and_cv": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_incongruity_ask(decision_maker, user_id),
            "choices": {
                "Yes": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_prompt_haha("ask_laughter_incongruity_haha", "ask_laughter_incongruity_no_haha"),
                "No": "no_incongruity_cv_no_haha",
                "Not sure": "reminder_incongruity",
            },
            "protocols": {
                "Yes": [],
                "No": [], 
                "Not sure": []
            },
        },

        "no_incongruity_cv_no_haha": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_no_incongruity_respond(decision_maker, user_id),
            "choices": {
                "continue": "ask_feel_pre_cv", 
            },
            "protocols": {
                "continue": [],
            }
        },
        
        "ask_feel_pre_cv": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_try_contrasting_views_ask(decision_maker, user_id),
            "choices": {
                "\U0001F600": "pre_cv_pos", 
                "\U0001F641": "pre_cv_neg"
            },
            "protocols": {
                "\U0001F600": [],
                "\U0001F641": [],
            }
        },
        

        "no_incongruity_cv_haha": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_no_incongruity_respond(decision_maker, user_id),
            "choices": {
                "Haha": "funny_no_incongruity",
                "That wasn't funny": "not_funny_no_incongruity"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_no_incongruity": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "ask_feel_pre_cv", 
            },
            "protocols": {
                "continue": [],
            }
        },

        "not_funny_no_incongruity": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "ask_feel_pre_cv", 
            },
            "protocols": {
                "continue": [],
            }
        },

        # 3) own laughter brand and feigning laughter: 
        # "ask_laughter_brand" (see above)
    }

    return QUESTIONS

def get_model_prompt_incongruity_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[incongruity_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format("").split("*")
    return question

def get_model_prompt_no_incongruity_respond(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[no_incongruity_respond].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format("").split("*")
    return question

def get_model_prompt_try_contrasting_views_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[try_contrasting_views_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format("").split("*")
    return question
