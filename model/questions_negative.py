from model.utterances import *
from model.questions_main import *

def get_negative_questions(decision_maker):

    QUESTIONS = {

        #################### MAIN SESSION (NEGATIVE)
        
        "underlying_reason_yes": {
            "model_prompt": try_laugh_ask,
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
            "model_prompt": laugh_off_low_ask,
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
            "model_prompt": [can_laugh_off_low_pos, feeling_pre_exercise_ask],
            "choices": {
                "\U0001F600": "try_pre_protocol_pos_no_haha",
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
            "model_prompt": [neg_repond, not_contempt_note], 
            "choices": {
                "Sure": "try_pre_protocol_neg_no_haha", 
                "How can I stop this?": "try_pre_protocol_neg_no_contempt",
            },
            "protocols": {
                "Sure": [],
                "How can I stop this?": []
            },
        },
        
        "encourage_laughter": {
            "model_prompt": [laugh_off_low_neg_respond, try_exercise_encourage],
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        "pre_laughter_neg": {
            # TODO: check
            "model_prompt": further_clarification_ask,
            "choices": {
                "yes": "clarify_laughter_haha",
                "no": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre(user_id) 
            },
            "protocols": {
                "yes": [],
                "no": [], 
            },
        },

        "clarify_laughter_haha": {
            "model_prompt": laugh_off_low_inform,
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
            "model_prompt": laugh_off_low_inform,
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
            "model_prompt": explore_reason_ask,
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
            "model_prompt": reason_incongruity_ask,
            "choices": {
                "Yes": "ask_laughter_incongruity_no_haha",
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
            "model_prompt": reason_error_ask,
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
            "model_prompt": incongruity_inform,
            "choices": {
                "continue": "explore_trigger_yes_no_unsure", 
            },
            "protocols": {
                "continue": []
            },
        },

        "explore_trigger_yes_no_unsure": {
            "model_prompt": cont_reason_incongruity_ask,
            "choices": {
                "yes": "ask_laughter_incongruity_no_haha", # trigger is incongruity -> SKIP TO MINI-SESSION
                "no": "trigger_not_incongruity",
            },
            "protocols": {
                "yes": [],
                "no": [],
            },
        },

        "trigger_not_error": {
            "model_prompt": explore_involved_reason_ask,
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
            "model_prompt": reason_setback_ask,
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
            "model_prompt": reason_hardship_ask,
            "choices": {
                "yes": "ask_accept_hardship_no_haha", 
                "no": "trigger_not_hardship_haha",
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "trigger_not_hardship_haha": {
            "model_prompt": not_find_reason_reassure, 
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
            "model_prompt": not_find_reason_reassure, 
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