from model.utterances import *
from model.questions_main import *
from model.questions_mini_session import *
from model.questions_positive import *
from model.questions_reused import *

def get_negative_questions(decision_maker):

    #################### MAIN SESSION (NEGATIVE) ####################

    QUESTIONS = {
        
        "underlying_reason_yes": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_try_laugh_ask(decision_maker, user_id),
            "choices": {
                "yes": "pre_laughter_pos",
                "no": "pre_laughter_neg", 
            },
            "protocols": {
                #"yes": [decision_maker.PROTOCOL_TITLES[9], decision_maker.PROTOCOL_TITLES[10], decision_maker.PROTOCOL_TITLES[11]], #change here?
                #[decision_maker.PROTOCOL_TITLES[k] for k in decision_maker.positive_protocols],
                "yes": [],
                "no": [],
            },
        },

        "pre_laughter_pos": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_laugh_off_low_ask(decision_maker, user_id),
            "choices": {
                "Superiority": "propose_laugh_off",
                "Incongruity": "propose_laugh_off",
                "Playful": "propose_laugh_off",
                "A combination of these": "propose_laugh_off",
                "Other": "propose_laugh_off",

            },
            "protocols": {
                #"yes": [decision_maker.PROTOCOL_TITLES[9], decision_maker.PROTOCOL_TITLES[10], decision_maker.PROTOCOL_TITLES[11]], #change here?
                #[decision_maker.PROTOCOL_TITLES[k] for k in decision_maker.positive_protocols],
                "Superiority": [],
                "Incongruity": [],
                "Playful": [],
                "A combination of these": [],
                "Other": [],
            },
        },

        "propose_laugh_off": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_can_laugh_off_low_ask_feeling_pre(decision_maker, user_id),
            "choices": {
                "\U0001F600": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_prompt_haha("try_pre_protocol_pos_haha", "try_pre_protocol_pos_no_haha"),
                "\U0001F641": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt(user_id)
            },
            "protocols": {
                #"yes": [decision_maker.PROTOCOL_TITLES[9], decision_maker.PROTOCOL_TITLES[10], decision_maker.PROTOCOL_TITLES[11]], #change here?
                #[decision_maker.PROTOCOL_TITLES[k] for k in decision_maker.positive_protocols],
                "\U0001F600": [],
                "\U0001F641": [],
            },
        },

        "remind_contempt_pre_laughter": {
            # TODO: what response?
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_neg_respond_not_contempt_note(decision_maker, user_id), 
            "choices": {
                "Sure": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_prompt_haha("try_pre_protocol_neg_haha", "try_pre_protocol_neg_no_haha"), 
                "How can I stop this?": "try_pre_protocol_neg_no_contempt",
            },
            "protocols": {
                "Sure": [],
                "How can I stop this?": []
            },
        },
        
        "encourage_laughter": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_laugh_off_low_neg_try(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        "pre_laughter_neg": {
            # TODO: check
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_further_clarification_ask(decision_maker, user_id),
            "choices": {
                "yes": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_prompt_haha("clarify_laughter_haha", "clarify_laughter_no_haha"),
                "no": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre(user_id) 
            },
            "protocols": {
                "yes": [],
                "no": [], 
            },
        },

        "clarify_laughter_haha": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_laugh_off_low_inform(decision_maker, user_id),
            "choices": {
                "Haha": "funny_clarify_laughter",
                "That wasn't funny": "not_funny_clarify_laughter"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_clarify_laughter": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre(user_id)
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_clarify_laughter": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre(user_id),
            },
            "protocols": {
                "continue": [],
            },
        },


        "clarify_laughter_no_haha": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_laugh_off_low_inform(decision_maker, user_id),
            "choices": {
                "continue": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre(user_id) 
            },
            "protocols": {
                #"yes": [decision_maker.PROTOCOL_TITLES[9], decision_maker.PROTOCOL_TITLES[10], decision_maker.PROTOCOL_TITLES[11]], #change here?
                #[decision_maker.PROTOCOL_TITLES[k] for k in decision_maker.positive_protocols],
                "continue": [],
            },
        },

        "underlying_reason_no": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_explore_reason_ask(decision_maker, user_id),
            "choices": {
                "yes": "explore_trigger_yes",
                "no": "continue_curr_not_willing",
            },
            "protocols": {
                #"yes": [decision_maker.PROTOCOL_TITLES[9], decision_maker.PROTOCOL_TITLES[10], decision_maker.PROTOCOL_TITLES[11]], #change here?
                #[decision_maker.PROTOCOL_TITLES[k] for k in decision_maker.positive_protocols],
                "yes": [],
                "no": []
            },
        },

        "explore_trigger_yes": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_reason_incongruity_ask(decision_maker, user_id),
            "choices": {
                "Yes": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_prompt_haha("ask_laughter_incongruity_haha", "ask_laughter_incongruity_no_haha"),
                "No": "trigger_not_incongruity",
                "Not sure": "trigger_unsure_incongruity"
            },
            "protocols": {
                "Yes": [],
                "No": [],
                "Not sure": []
            },
        },

        "trigger_not_incongruity": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_reason_error_ask(decision_maker, user_id),
            "choices": {
                "yes": "ask_feel_pre_error", 
                "no": "trigger_not_error",
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "trigger_unsure_incongruity": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_incongruity_inform(decision_maker, user_id),
            "choices": {
                "continue": "explore_trigger_yes_no_unsure", 
            },
            "protocols": {
                "continue": []
            },
        },

        "explore_trigger_yes_no_unsure": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_cont_reason_incongruity_ask(decision_maker, user_id),
            "choices": {
                "yes": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_prompt_haha("ask_laughter_incongruity_haha", "ask_laughter_incongruity_no_haha"), # trigger is incongruity -> SKIP TO MINI-SESSION
                "no": "trigger_not_incongruity",
            },
            "protocols": {
                "yes": [],
                "no": [],
            },
        },

        "trigger_not_error": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_explore_involved_reason_ask(decision_maker, user_id),
            "choices": {
                "yes": "ask_trigger_setback", 
                "no": "continue_curr_not_willing",
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "ask_trigger_setback": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_reason_setback_ask(decision_maker, user_id),
            "choices": {
                "yes": "ask_laughter_setback", 
                "no": "trigger_not_setback",
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "trigger_not_setback": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_reason_hardship_ask(decision_maker, user_id),
            "choices": {
                "yes": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_prompt_haha("ask_accept_hardship_haha", "ask_accept_hardship_no_haha"), 
                "no": "trigger_not_hardship_haha",
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "trigger_not_hardship_haha": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_find_reason_reassure(decision_maker, user_id),
            "choices": {
                "Haha": "funny_not_hardship",
                "That wasn't funny": "not_funny_not_hardship"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_not_hardship": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_can't_do", 
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_not_hardship": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_can't_do", 
            },
            "protocols": {
                "continue": [],
            },
        },

        "trigger_not_hardship_no_haha": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_find_reason_reassure(decision_maker, user_id), 
            "choices": {
                "continue": "continue_curr_can't_do", 
            },
            "protocols": {
                "continue": [],
            },
        },

        #################### END MAIN SESSION (NEGATIVE)

    }

    return QUESTIONS

def get_model_prompt_try_laugh_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[try_laugh_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question
        
def get_model_prompt_laugh_off_low_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[laugh_off_low_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_can_laugh_off_low_ask_feeling_pre(decision_maker, user_id):
    name = decision_maker.users_names[user_id]
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[can_laugh_off_low_pos].dropna()
    column2 = data[feeling_pre_exercise_ask].dropna()
    my_string1 = decision_maker.get_best_sentence_new(column1, prev_qs)
    my_string2 = decision_maker.get_best_sentence_new(column2, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    question = "*".join([my_string1, my_string2]).format(name).split("*")
    return question

def get_model_prompt_neg_respond_not_contempt_note(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[neg_respond].dropna()
    column2 = data[not_contempt_note].dropna()
    my_string1 = decision_maker.get_best_sentence_new(column1, prev_qs)
    my_string2 = decision_maker.get_best_sentence_new(column2, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    question = "*".join([my_string1, my_string2]).format().split("*")
    return question

def get_model_prompt_laugh_off_low_neg_try(decision_maker, user_id):
    name = decision_maker.users_names[user_id]
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column1 = data[laugh_off_low_neg_respond].dropna()
    column2 = data[try_exercise_encourage].dropna()
    my_string1 = decision_maker.get_best_sentence_new(column1, prev_qs)
    my_string2 = decision_maker.get_best_sentence_new(column2, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string1)
        decision_maker.recent_questions[user_id].append(my_string2)
    question = "*".join([my_string1, my_string2]).format(name).split("*")
    return question

def get_model_prompt_further_clarification_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[further_clarification_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_laugh_off_low_inform(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[laugh_off_low_inform].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_explore_reason_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[explore_reason_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_reason_incongruity_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[reason_incongruity_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_reason_error_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[reason_incongruity_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_incongruity_inform(decision_maker, user_id):
    name = decision_maker.users_names[user_id]
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[incongruity_inform].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format(name).split("*")
    return question


def get_model_prompt_cont_reason_incongruity_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[cont_reason_incongruity_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_explore_involved_reason_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[explore_involved_reason_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_reason_setback_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[reason_setback_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_reason_hardship_ask(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[hardship_ask].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question

def get_model_prompt_not_find_reason_reassure(decision_maker, user_id):
    prev_qs = pd.DataFrame(decision_maker.recent_questions[user_id],columns=['sentences'])
    data = decision_maker.dataset
    column = data[not_find_reason_reassure].dropna()
    my_string = decision_maker.get_best_sentence_new(column, prev_qs)
    if len(decision_maker.recent_questions[user_id]) < 50:
        decision_maker.recent_questions[user_id].append(my_string)
    else:
        decision_maker.recent_questions[user_id] = []
        decision_maker.recent_questions[user_id].append(my_string)
    question = my_string.format().split("*")
    return question