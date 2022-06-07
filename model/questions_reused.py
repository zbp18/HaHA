from model.utterances import *
from model.questions_main import *

def get_reused_questions(decision_maker):
    
    #################### REUSED PARTS OF CONVERSATIO ####################
    
    QUESTIONS = {            

        # continue exploring

        "continue_curr_can't_do": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_more_exercises_ask(decision_maker, user_id),
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
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_pos_respond_more_exercises(decision_maker, user_id),
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
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_more_exercises_ask(decision_maker, user_id),
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
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_more_exercises_ask(decision_maker, user_id),
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
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_pos_respond_joke(decision_maker, user_id), 
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
                "continue": "continue_curr_willing"
            },
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
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_pos_pre_exercise_respond(decision_maker, user_id), 
            "choices": {
                "continue": "continue_curr_willing", # function that returns next prompt (random based on user's choice, emotion and current level)
            },
            "protocols": {
                "continue": [],
            },
        },

        # encourage practice

        "try_pre_protocol_pos_haha": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_pos_respond_try_exercise(decision_maker, user_id), 
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
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_pos_respond_try_exercise(decision_maker, user_id), 
            "choices": {
                "continue": "continue_curr_willing"
            },
            "protocols": {
                "continue": [],
            },
        },

        "try_pre_protocol_neg_haha": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_try_exercise_encourage(decision_maker, user_id),
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
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_try_exercise_encourage(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        }, 

        "try_pre_protocol_neg_no_contempt":{
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_pos_no_contempt_try_exercise(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        "try_laughter_pre_protocol_pos": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_try_exercise_encourage(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        "try_post_protocol_pos": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_pos_respond_try_exercise_again(decision_maker, user_id), 
            "choices": {
                "continue": "continue_curr_willing"    
            },
            "protocols": {
                "continue": [],
            },
        },

        "try_post_protocol_neg":{
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_try_exercise_again_encourage(decision_maker, user_id), 
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        # more explanation
        "review_post_protocol_neg": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_neg_respond_protocols_remind(decision_maker, user_id), 
            "choices": {
                "continue": "try_post_protocol_neg", 
            },
            "protocols": {
                "continue": [],
            },
        },

        # no contempt 

        "remind_contempt_post_protocol":{
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_contempt_note(decision_maker, user_id), 
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
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_no_contempt_inform_try_again(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        "remind_contempt_pre_protocol_haha":{
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_contempt_note(decision_maker, user_id), 
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
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond_make_sense(decision_maker, user_id),
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
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond_make_sense(decision_maker, user_id),
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
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_contempt_note(decision_maker, user_id), 
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
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_no_contempt_inform(decision_maker, user_id), 
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        },
    }

    return QUESTIONS

def get_model_prompt_more_exercises_ask(decision_maker, user_id):
    name = decision_maker.users_names[user_id]
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[more_exercises_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format(name).split("*")
    return question
#pos_pre_exercise_respond
def get_model_prompt_pos_respond_more_exercises(decision_maker, user_id):
    name = decision_maker.users_names[user_id]
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[pos_respond].dropna()
    column2 = data[more_exercises_ask].dropna()
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

def get_model_prompt_pos_respond(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[pos_respond].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_pos_respond_joke(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[pos_pre_exercise_respond_joke].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question
    
def get_model_prompt_pos_pre_exercise_respond(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[pos_pre_exercise_respond].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_pos_respond_try_exercise(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[pos_respond].dropna()
    column2 = data[try_exercise_encourage].dropna()
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
    
def get_model_prompt_try_exercise_encourage(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[try_exercise_encourage].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_pos_no_contempt_try_exercise(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[no_contempt_inform].dropna()
    column2 = data[try_exercise_encourage].dropna()
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

def get_model_prompt_pos_respond_try_exercise_again(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[pos_respond].dropna()
    column2 = data[try_exercise_again_encourage].dropna()
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

def get_model_prompt_try_exercise_again_encourage(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[try_exercise_again_encourage].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_neg_respond_protocols_remind(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[neg_respond].dropna()
    column2 = data[protocols_remind].dropna()
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

def get_model_prompt_not_contempt_note(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[not_contempt_note].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_no_contempt_inform_try_again(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[no_contempt_inform].dropna()
    column2 = data[try_exercise_again_encourage].dropna()
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

def get_model_prompt_funny_respond_make_sense(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[funny_respond].dropna()
    column2 = data[cont_make_sense_ask].dropna()
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

def get_model_prompt_not_funny_respond_make_sense(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[not_funny_respond].dropna()
    column2 = data[cont_make_sense_ask].dropna()
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

def get_model_prompt_no_contempt_inform(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[no_contempt_inform].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs, user_id)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question