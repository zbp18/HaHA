from model.utterances import *
from model.questions_main import *

def get_reused_questions(decision_maker):

    QUESTIONS = {            

        #################### REUSED PARTS OF CONVERSATION ####################
        
        # continue exploring

        "continue_curr_can't_do": {
            "model_prompt": more_exercises_ask,
            "choices": {
                "yes": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_mini_session(user_id, "can't_do"), # function that returns next prompt (random based on user's choice, emotion and current level)
                "no": "review_any_session",#"lambda user_id, db_session, curr_session, app: decision_maker.end_session(user_id)"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "empathetic_continue_curr_can't_do": {
            "model_prompt": [pos_respond, more_exercises_ask],
            "choices": {
                "yes": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_mini_session(user_id, "can't_do"), # function that returns next prompt (random based on user's choice, emotion and current level)
                "no": "review_any_session" #lambda user_id, db_session, curr_session, app: decision_maker.end_session(user_id)
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "continue_curr_not_willing": {
            "model_prompt": more_exercises_ask,
            "choices": {
                "yes": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_mini_session(user_id, "not_willing"), # function that returns next prompt (random based on user's choice, emotion and current level)
                "no": "review_any_session"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "continue_curr_willing": {
            "model_prompt": more_exercises_ask,
            "choices": {
                "yes": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_mini_session(user_id, "willing"), # function that returns next prompt (random based on user's choice, emotion and current level)
                "no": "review_any_session"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "continue_pos_pre_protocol_haha": {
            "model_prompt": pos_respond, 
            "choices": {
                "Haha": "funny_pos_pre_protocol",
                "That wasn't funny": "not_funny_pos_pre_protocol",
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_pos_pre_protocol": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id), 
            "choices": {
                "continue": "continue_curr_willing"                },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_pos_pre_protocol": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_willing"
            },
            "protocols": {
                "continue": [],
            },
        },

        "continue_pos_pre_protocol_no_haha": {
            "model_prompt": pos_pre_exercise_respond, 
            "choices": {
                "continue": "continue_curr_willing", # function that returns next prompt (random based on user's choice, emotion and current level)
            },
            "protocols": {
                "continue": [],
            },
        },

        # encourage practice

        "try_pre_protocol_pos_haha": {
            "model_prompt": [pos_respond, try_exercise_encourage], 
            "choices": {
                "Haha": "funny_try_pre_pos",
                "That wasn't funny": "not_funny_try_pre_pos"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_try_pre_pos": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_try_pre_pos": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        "try_pre_protocol_pos_no_haha": {
            "model_prompt": [pos_respond, try_exercise_encourage], 
            "choices": {
                "continue": "continue_curr_willing"
            },
            "protocols": {
                "continue": [],
            },
        },

        "try_pre_protocol_neg_haha": {
            "model_prompt": try_exercise_encourage,
            "choices": {
                "Haha": "funny_try_pre_neg",
                "That wasn't funny": "not_funny_try_pre_neg"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_try_pre_neg": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_try_pre_neg": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        }, 

        "try_pre_protocol_neg_no_haha": {
            "model_prompt": try_exercise_encourage,
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        }, 

        "try_pre_protocol_neg_no_contempt":{
            "model_prompt": [no_contempt_inform, try_exercise_encourage],
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        "try_laughter_pre_protocol_pos": {
            "model_prompt": try_exercise_encourage,
            "choices": {
                "continue": "continue_curr_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        "try_post_protocol_pos": {
            "model_prompt": [pos_respond, try_exercise_again_encourage], 
            "choices": {
                "continue": "continue_curr_willing"    
            },
            "protocols": {
                "continue": [],
            },
        },

        "try_post_protocol_neg":{
            "model_prompt": try_exercise_again_encourage, 
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        # more explanation
        "review_post_protocol_neg": {
            "model_prompt": [neg_repond, protocols_remind],
            "choices": {
                "continue": "try_post_protocol_neg", 
            },
            "protocols": {
                "continue": [],
            },
        },

        # no contempt 

        "remind_contempt_post_protocol":{
            "model_prompt": not_contempt_note, 
            "choices": {
                "Sure": "try_post_protocol_neg", 
                "How can I stop this?": "explain_contempt_post_protocol",
            },
            "protocols": {
                "Sure": [],
                "How can I stop this?": []
            },
        },

        "explain_contempt_post_protocol":{
            "model_prompt": [no_contempt_inform, try_exercise_again_encourage], 
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        "remind_contempt_pre_protocol_haha":{
            "model_prompt": not_contempt_note, 
            "choices": {
                "Haha": "funny_contempt_pre_protocol",
                "That wasn't funny": "not_funny_contempt_pre_protocol"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_contempt_pre_protocol": {
            "model_prompt": [funny_respond, cont_make_sense_ask],
            "choices": {
                "yes": "continue_curr_not_willing", 
                "no": "explain_contempt_pre_protocol",
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "not_funny_contempt_pre_protocol": {
            "model_prompt": [not_funny_respond, cont_make_sense_ask],
            "choices": {
                "yes": "continue_curr_not_willing", 
                "no": "explain_contempt_pre_protocol",
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "remind_contempt_pre_protocol_no_haha":{
            "model_prompt": not_contempt_note, 
            "choices": {
                "Sure": "continue_curr_not_willing", 
                "How can I stop this?": "explain_contempt_pre_protocol",
            },
            "protocols": {
                "Sure": [],
                "How can I stop this?": []
            },
        },

        "explain_contempt_pre_protocol":{
            "model_prompt": no_contempt_inform, 
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        },
    }

    return QUESTIONS