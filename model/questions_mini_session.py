from model.utterances import *
from model.questions_main import *

def get_mini_sessions_questions(decision_maker):

    QUESTIONS = {

        #################### MINI SESSIONS ####################

        # playful mode

        "ask_playful_mode_haha": {
            "model_prompt": playful_ask,
            "choices": {
                "Haha": "funny_playful",
                "That wasn't funny": "not_funny_playful"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_playful": {
            "model_prompt": [funny_respond, cont_playful_ask],
            "choices": {
                "yes": "check_acknowledge_achievements",
                "no": "inform_playful"
            },
            "protocols": {
                "yes": [decision_maker.PROTOCOL_TITLES[1], decision_maker.PROTOCOL_TITLES[2]],
                "no": [decision_maker.PROTOCOL_TITLES[1], decision_maker.PROTOCOL_TITLES[2]]
            },
        },

        "not_funny_playful": {
            "model_prompt": [not_funny_respond, cont_playful_ask],
            "choices": {
                "yes": "check_acknowledge_achievements",
                "no": "inform_playful"
            },
            "protocols": {
                "yes": [decision_maker.PROTOCOL_TITLES[1], decision_maker.PROTOCOL_TITLES[2]],
                "no": [decision_maker.PROTOCOL_TITLES[1], decision_maker.PROTOCOL_TITLES[2]]
            },
        },


        "ask_playful_mode_no_haha": {
            "model_prompt": playful_ask,
            "choices": {
                "yes": "check_acknowledge_achievements",
                "no": "inform_playful"
            },
            "protocols": {
                "yes": [decision_maker.PROTOCOL_TITLES[1], decision_maker.PROTOCOL_TITLES[2]],
                "no": [decision_maker.PROTOCOL_TITLES[1], decision_maker.PROTOCOL_TITLES[2]]
            },
        },

        "check_acknowledge_achievements": {
            "model_prompt": pos_respond,
            #TODO: should we have choices: haha & not funny
            "choices": {
                "continue": lambda user_id, db_session, curr_session, app: decision_maker.check_acknowledge_achievements(user_id),
            },
            "protocols": {
                "continue": [decision_maker.PROTOCOL_TITLES[1], decision_maker.PROTOCOL_TITLES[2]],
            },
        },

        "inform_playful": {
            "model_prompt": playful_mind_inform,
            "choices": {
                "I see": "explore_playful",
                "Can I have an example": "example_playful",
            },
            "protocols": {
                "I see": [],
                "Can I have an example": [],
            },
        },

        "explore_playful":{
            "model_prompt": playful_mode_other,
            "choices": {
                "continue": "ask_song",
            },
            "protocols": {
                "continue": [],
            },
        },

        "ask_song":{
            # TODO: should we add a delay
            "model_prompt": any_song_ask,
            "choices": {
                "yes": "response_to_song_haha",
                "no": "recommend_song_haha"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "response_to_song_haha": {
            "model_prompt": has_song_respond,
            "choices": {
                "Haha": "funny_rec_playful",
                "That wasn't funny": "not_funny_rec_playful"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_rec_playful": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "recommend_playful_protocol",
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_rec_playful": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "recommend_playful_protocol",
            },
            "protocols": {
                "continue": [],
            },
        },


        "response_to_song_not_haha": {
            "model_prompt": has_song_respond,
            "choices": {
                "continue": "recommend_playful_protocol",
            },
            "protocols": {
                "continue": [],
            },
        },

        "recommend_playful_protocol": {
            "model_prompt": [playful_face_inform, feeling_pre_exercise_ask],
            "choices": {
                "\U0001F600": "continue_pos_pre_protocol_no_haha",
                "\U0001F641": "pre_playful_neg"
            },
            "protocols": {
                "\U0001F600": [],
                "\U0001F641": [],
            },
        },

        "recommend_song_haha": {
            "model_prompt": no_song_respond,
            "choices": {
                "Haha": "funny_rec_song",
                "That wasn't funny": "not_funny_rec_song"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_rec_song": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "recommend_playful_protocol",
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_rec_song": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "recommend_playful_protocol",
            },
            "protocols": {
                "continue": [],
            },
        },

        "recommend_song_not_haha": {
            "model_prompt": no_song_respond,
            "choices": {
                "continue": "recommend_playful_protocol",
            },
            "protocols": {
                "continue": [],
            },
        },

        "pre_playful_neg": {
            "model_prompt": [protocols_remind, try_exercise_encourage],
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        "example_playful": {
            "model_prompt": [playful_mind_inform_eg, try_exercise_encourage],
            "choices": {
                "continue": "explore_playful"
            },
            "protocols": {
                "continue": []
            },
        },

        # self-glory

        "ask_self_glory_haha": {
            "model_prompt": acknowledge_achievements_ask,
            "choices": {
                "Haha": "funny_sg",
                "That wasn't funny": "not_funny_sg"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_sg": {
            "model_prompt": [funny_respond, cont_self_glory_ask],
            "choices": {
                "yes": "ask_congratulate_with_smile",
                "no": "propose_congratulate_with_smile_no_haha"
            },
            "protocols": {
                "yes": [decision_maker.PROTOCOL_TITLES[3]],
                "no": [decision_maker.PROTOCOL_TITLES[3]]
            },
        },

        "not_funny_sg": {
            "model_prompt": [not_funny_respond, cont_self_glory_ask],
            "choices": {
                "yes": "ask_congratulate_with_smile",
                "no": "propose_congratulate_with_smile_no_haha"
            },
            "protocols": {
                "yes": [decision_maker.PROTOCOL_TITLES[3]],
                "no": [decision_maker.PROTOCOL_TITLES[3]]
            },
        },


        "ask_self_glory_not_haha": {
            "model_prompt": acknowledge_achievements_ask,
            "choices": {
                "yes": "ask_congratulate_with_smile",
                "no": "propose_congratulate_with_smile_haha"
            },
            "protocols": {
                "yes": [decision_maker.PROTOCOL_TITLES[3]],
                "no": [decision_maker.PROTOCOL_TITLES[3]]
            },
        },

        "ask_congratulate_with_smile": {
            "model_prompt": self_glory_encourage,
            "choices": {
                "yes": "ask_feel_post_sg",
                "no": "propose_sg_and_eg"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "ask_feel_post_sg": {
            # TODO: change choices to better, worse or the same? - for now the same and worse is same 
            "model_prompt": feeling_post_exercise_ask,
            "choices": {
                "Better": "try_post_protocol_pos", 
                "No change": "review_post_protocol_neg",
                "Worse": "review_post_protocol_neg",
            },
            "protocols": {
                "Better": [],
                "No change": [],
                "Worse": [],
            },
        },
        
        "propose_sg_and_eg": {
            "model_prompt": try_self_glory_ask,
            "choices": {
                "\U0001F600": "continue_pos_pre_protocol_no_haha", 
                "\U0001F641": "pre_sg_neg"
            },
            "protocols": {
                "\U0001F600": [],
                "\U0001F641": [],
            }
        },

        "pre_sg_neg": {
            # TODO: do we want neg_repond?
            "model_prompt": [neg_repond, further_clarification_ask],
            "choices": {
                "yes": "further_clarify_sg",
                "no": "continue_curr_not_willing"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "further_clarify_sg": {
            "model_prompt": [theories_inform, protocols_remind],
            "choices": {
                "continue": "continue_curr_not_willing"
            },
            "protocols": {
                "continue": [],
            },
        },

        "propose_congratulate_with_smile_haha": {
            "model_prompt": self_glory_encourage,
            "choices": {
                "Haha": "funny_prop_congrat",
                "That wasn't funny": "not_funny_prop_congrat"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_prop_congrat": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_can't_do"
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_prop_congrat": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_can't_do"
            },
            "protocols": {
                "continue": [],
            },
        },

        "propose_congratulate_with_smile_no_haha": {
            "model_prompt": self_glory_encourage,
            "choices": {
                "continue": "continue_curr_can't_do"
            },
            "protocols": {
                "continue": [],
            },
        },

        # incongruity

        "ask_incongruity": {
            "model_prompt": incongruity_ask,
            "choices": {
                "Yes": "ask_laughter_incongruity_haha",
                "No": "no_incongruity",
                "Not sure": "reminder_incongruity",
            },
            "protocols": {
                "Yes": [decision_maker.PROTOCOL_TITLES[4], decision_maker.PROTOCOL_TITLES[5], decision_maker.PROTOCOL_TITLES[6]],
                "No": [decision_maker.PROTOCOL_TITLES[4], decision_maker.PROTOCOL_TITLES[5], decision_maker.PROTOCOL_TITLES[6]], 
                "Not sure": [decision_maker.PROTOCOL_TITLES[4], decision_maker.PROTOCOL_TITLES[5], decision_maker.PROTOCOL_TITLES[6]]
            },
        },

        "ask_laughter_incongruity_haha": {
            "model_prompt": laugh_off_ask_joke, # are you able to laugh this off
            "choices": {
                "Haha": "funny_ask_laugh_incong",
                "That wasn't funny": "not_funny_ask_laugh_incong"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_ask_laugh_incong": {
            "model_prompt": [funny_respond, cont_laugh_off_ask],
            "choices": {
                "yes": "try_laughter_pre_protocol_pos", 
                "no": "pre_incongruity_neg"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "not_funny_ask_laugh_incong": {
            "model_prompt": [not_funny_respond, cont_laugh_off_ask],
            "choices": {
                "yes": "try_laughter_pre_protocol_pos", 
                "no": "pre_incongruity_neg"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "ask_laughter_incongruity_no_haha": {
            "model_prompt": laugh_off_ask_joke, # are you able to laugh this off
            "choices": {
                "yes": "try_laughter_pre_protocol_pos", 
                "no": "pre_incongruity_neg"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "pre_incongruity_neg": {
            #TODO check this
            "model_prompt": further_clarification_ask,
            "choices": {
                "yes": "further_clarify_incongruity",
                "no": "try_laughter_incongruity",
            },
            "protocols": {
                "yes": [],
                "no": [], 
            },
        },

        "further_clarify_incongruity": {
            "model_prompt": [incongruity_remind, protocols_remind],
            "choices": {
                "continue": "try_laughter_incongruity",
            },
            "protocols": {
                "continue": [],
            },
        },

        "try_laughter_incongruity": {
            "model_prompt": laugh_incongruity_inform, # TODO how does that sound? + -> great - come back tell me
            "choices": {
                "continue": "ask_feel_pre_incongruity", 
            },
            "protocols": {
                "continue": [],
            },
        },

        "ask_feel_pre_incongruity": {
            "model_prompt": feeling_pre_exercise_ask,
            "choices": {
                "\U0001F600": "continue_pos_pre_protocol_no_haha",
                "\U0001F610": "continue_curr_not_willing",
                "\U0001F641": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre(user_id),

            },
            "protocols": {
                "\U0001F600": [],
                "\U0001F610": [],
                "\U0001F641": [],
            }
        },

        "no_incongruity": {
            "model_prompt": [no_incongruity_respond, more_exercises_ask],
            "choices": {
                "yes": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_mini_session(user_id, "can't_do"), # function that returns next prompt (random based on user's choice, emotion and current level)
                "no": "review_any_session"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },          

        "reminder_incongruity": {
            "model_prompt": incongruity_inform,
            "choices": {
                "continue": "ask_incongruity_no_unsure",
            },
            "protocols": {
                "continue": [],
            },
        },

        "ask_incongruity_no_unsure": {
            "model_prompt": incongruity_ask,
            "choices": {
                "yes": "ask_laughter_incongruity_no_haha",
                "no": "continue_curr_can't_do",
            },
            "protocols": {
                "yes": [],
                "no": [], 
            },
        },

        # contrasting views

        "ask_feel_pre_cv": {
            "model_prompt": try_contrasting_views_ask,
            "choices": {
                # add emojis
                "\U0001F600": "pre_cv_pos", 
                "\U0001F641": "pre_cv_neg"
            },
            "protocols": {
                "\U0001F600": [],
                "\U0001F641": [],
            }
        },

        "pre_cv_pos": {
            "model_prompt": [pos_respond, further_clarification_ask], 
            "choices": {
                "yes": "further_clarify_cv_not_haha", 
                "no": "try_laughter_pre_protocol_pos",
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "further_clarify_cv_haha": {
            #TODO: should we perform a search?
            "model_prompt": contrasting_views_inform, # extension - wiki search if user would like to know more
            "choices": {
                "Haha": "funny_cv",
                "That wasn't funny": "not_funny_cv"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_cv": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "confirm_understand_cv",
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_cv": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "confirm_understand_cv",
            },
            "protocols": {
                "continue": [],
            },
        },

        "confirm_understand_cv": {
            "model_prompt": feeling_pre_exercise_ask,
            "choices": {
                "\U0001F600": "try_pre_protocol_neg_haha", 
                "\U0001F641": "explain_cv"
            },
            "protocols": {
                "\U0001F600": [],
                "\U0001F641": [],
            }
        },

        "further_clarify_cv_not_haha": {
            #TODO: should we perform a search?
            "model_prompt": contrasting_views_inform, # extension - wiki search if user would like to know more
            "choices": {
                "Sounds interesting": "try_pre_protocol_neg_haha",
                "What?": "explain_cv",
            },
            "protocols": {
                "Sounds interesting": [],
                "What?": [],
            },
        },

        "explain_cv": {
            #TODO: should we perform a search?
            "model_prompt": [protocols_remind, try_exercise_encourage],
            "choices": {
                "continue": "continue_curr_can't_do",
            },
            "protocols": {
                "continue": [],
            },
        },    

        "pre_cv_neg": {
            #TODO
            "model_prompt": further_clarification_ask,
            "choices": {
                "yes": "further_clarify_cv_haha",
                "no": "try_pre_protocol_neg_haha",
            },
            "protocols": {
                "yes": [],
                "no": [], 
            },
        },    

        # own laughter brand

        "ask_laughter_brand": {
            "model_prompt": laughter_brand_ask,
            "choices": {
                "yes": "ask_feel_post_lb",
                "no": "explain_lb"
            },
            "protocols": {
                "yes": [decision_maker.PROTOCOL_TITLES[8], decision_maker.PROTOCOL_TITLES[9]],
                "no": [decision_maker.PROTOCOL_TITLES[8], decision_maker.PROTOCOL_TITLES[9]]
            },
        },

        "ask_feel_post_lb": {
            "model_prompt": feeling_post_exercise_ask,
            "choices": {
                "Better": "post_lb_pos",
                "No change": "post_lb_neg",
                "Worse": "post_lb_neg", 
            },
            "protocols": {
                "Better": [],
                "No change": [],
                "Worse": [],
            },
        },

        "post_lb_pos": {
            "model_prompt": [pos_respond, build_laughter_brand_encourage],
            "choices": {
                "continue": "ask_explore_related",
            },
            "protocols": {
                "continue": [],
            },
        },

        "ask_explore_related": {
            "model_prompt": "Would you like to explore a related exercise?",
            "choices": {
                "yes": "ask_feigning_laughter",
                "no": "continue_curr_not_willing"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "ask_feigning_laughter": {
            "model_prompt": [feigning_laughter_introduce, feeling_pre_exercise_ask],
            "choices": {
                "\U0001F600": "continue_pos_pre_protocol_no_haha",
                "\U0001F641": "pre_fl_neg",
            },
            "protocols": {
                "\U0001F600": [],
                "\U0001F641": [],
            }
        },

        "pre_fl_neg": {
            # TODO: wording change? Perhaps some further clarification might help?
            "model_prompt": [neg_repond, further_clarification_ask],
            "choices": {
                "yes": "further_clarify_fl_haha",
                "no": "continue_curr_not_willing"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "further_clarify_fl_haha": {
            "model_prompt": feigning_laughter_inform,
            "choices": {
                "Haha": "funny_fl",
                "That wasn't funny": "not_funny_fl"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_fl": {
            "model_prompt": [funny_respond, protocols_remind],
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_fl": {
            "model_prompt": [not_funny_respond, protocols_remind],
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        },

        "further_clarify_fl_no_haha": {
            "model_prompt": feigning_laughter_inform,
            "choices": {
                "continue": "look_sheet_fl",
            },
            "protocols": {
                "continue": [],
            },
        },

        "look_sheet_fl": {
            "model_prompt": [protocols_remind, more_exercises_ask],
            "choices": {
                "yes": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_mini_session(user_id, "not_willing"), # function that returns next prompt (random based on user's choice, emotion and current level)
                "no": "review_any_session"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "post_lb_neg": {
            "model_prompt": [neg_repond, laughter_brand_inform_use],
            "choices": {
                "continue": "ask_explore_related",
            },
            "protocols": {
                "continue": [],
            },
        },

        "explain_lb": {
            "model_prompt": [laughter_brand_inform],
            "choices": {
                "continue": "continue_explaining_lb",
            },
            "protocols": {
                "continue": [],
            },
        },

        "continue_explaining_lb": {
            "model_prompt": make_sense_ask,
            "choices": {
                "yes": "try_pre_lb_no_haha",
                "no": "further_clarify_lb"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "try_pre_lb_haha": {
            "model_prompt": [pos_respond, build_laughter_brand_encourage],
            "choices": {
                "Haha": "funny_lb",
                "That wasn't funny": "not_funny_lb"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "try_pre_lb_no_haha": {
            "model_prompt": [pos_respond, build_laughter_brand_encourage, 
            "Maybe don\'t try this at the zoo, though, as they might not let you out!"],
            "choices": {
                "continue": "explore_related_lb",
            },
            "protocols": {
                "continue": [],
            },
        },

        "explore_related_lb":{
            "model_prompt": explore_related_ask,
            "choices": {
                "yes": "ask_feigning_laughter",
                "no": "continue_curr_not_willing"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "further_clarify_lb": {
            "model_prompt": protocols_remind,
            "choices": {
                "continue": "encourage_try_lb",
            },
            "protocols": {
                "continue": [],
            },
        },

        "encourage_try_lb": {
            "model_prompt": build_laughter_brand_encourage,
            "choices": {
                "Haha": "funny_lb",
                "That wasn't funny": "not_funny_lb"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_lb": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "explore_related_lb",
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_lb": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "explore_related_lb",
            },
            "protocols": {
                "continue": [],
            },
        },

        # self-laughter

        "ask_recent_error": {
            "model_prompt": self_error_ask,
            "choices": {
                "yes": "ask_laugher_error", 
                "no": "no_error_haha",
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "ask_laugher_error": {  
            "model_prompt": laughed_off_ask,
            "choices": {
                "yes": "ask_feel_post_error", 
                "no": "encourage_laughter_error_haha",
            },
            "protocols": {
                "yes": [],
                "no": [], 
            },
        },

        "ask_feel_post_error": {  
            "model_prompt": feeling_post_exercise_ask,
            "choices": {
                "Better": "try_post_protocol_pos",
                "No change": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_post_error(user_id),
                "Worse": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_post_error(user_id),
            },
            "protocols": {
                "Better": [],
                "No change": [],
                "Worse": [],
            },
        },

        "remind_contempt_post_error": { 
            "model_prompt": [neg_repond, not_contempt_note], 
            "choices": {
                "Sure": "ask_fc_post_error", 
                "How can I stop this?": "how_not_contempt_post_error",
            },
            "protocols": {
                "Sure": [],
                "How can I stop this?": []
            },
        },

        "ask_fc_post_error": { 
            "model_prompt": further_clarification_ask,
            "choices": {
                "yes": "further_clarify_post_error_haha", 
                "no": "try_post_protocol_neg"
            }, 
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "further_clarify_post_error_haha": { 
            # TODO
            "model_prompt": self_error_clarify, 
            "choices": {
                "Haha": "funny_post_error",
                "That wasn't funny": "not_funny_post_error"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_post_error": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "fc_post_error",
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_post_error": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "fc_post_error",
            },
            "protocols": {
                "continue": [],
            },
        },

        "fc_post_error": {
            "model_prompt": [self_laughter_inform_eg, protocols_remind], 
            "choices": {
                "continue": "try_post_protocol_neg",
            },
            "protocols": {
                "continue": [],
            },
        },

        "further_clarify_post_error_no_haha": {
            # TODO
            "model_prompt": [self_error_clarify, self_laughter_inform_eg, protocols_remind], 
            "choices": {
                "continue": "try_post_protocol_neg",
            },
            "protocols": {
                "continue": [],
            },
        },

        "how_not_contempt_post_error":{
            "model_prompt": [no_contempt_inform, further_clarification_ask], 
            "choices": {
                "yes": "further_clarify_post_error_no_haha", 
                "no": "try_post_protocol_neg" 
            }, 
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "post_error_neg": { 
            "model_prompt": [neg_repond, further_clarification_ask],
            "choices": {
                "yes": "further_clarify_post_error_no_haha", 
                "no": "try_post_protocol_neg"
            }, 
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "encourage_laughter_error_haha": {
            "model_prompt": self_error_encourage_joke,
            "choices": {
                "Haha": "funny_enc_laugh_err",
                "That wasn't funny": "not_funny_enc_laugh_err"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_enc_laugh_err": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "ask_feel_pre_error",
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_enc_laugh_err": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "ask_feel_pre_error",
            },
            "protocols": {
                "continue": [],
            },
        },


        "encourage_laughter_error_no_haha": {
            "model_prompt": self_error_encourage_joke,
            "choices": {
                "continue": "ask_feel_pre_error",
            },
            "protocols": {
                "continue": [],
            },
        },

        "ask_feel_pre_error": {
            "model_prompt": feeling_pre_exercise_ask,
            "choices": {
                "\U0001F600": "continue_pos_pre_protocol_no_haha",
                "\U0001F610": "explain_laughter_error",
                "\U0001F641": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre_error(user_id),
            },
            "protocols": {
                "\U0001F600": [],
                "\U0001F610": [],
                "\U0001F641": [],
            }
        },

        "remind_contempt_pre_error": { 
            "model_prompt": [neg_repond, not_contempt_note], 
            "choices": {
                "Sure": "ask_fc_pre_error", 
                "How can I stop this?": "how_not_contempt_pre_error",
            },
            "protocols": {
                "Sure": [],
                "How can I stop this?": []
            },
        },

        "ask_fc_pre_error": { 
            "model_prompt": further_clarification_ask, 
            "choices": {
                "yes": "further_clarify_pre_error_no_haha",
                "no": "try_pre_protocol_neg_no_haha"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "how_not_contempt_pre_error":{
            "model_prompt": [no_contempt_inform, further_clarification_ask], 
            "choices": {
                "yes": "further_clarify_pre_error_no_haha", 
                "no": "try_pre_protocol_neg_no_haha" 
            }, 
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "pre_error_neg": {
            "model_prompt": [neg_repond, further_clarification_ask], 
            "choices": {
                "yes": "further_clarify_pre_error_no_haha",
                "no": "try_pre_protocol_neg_no_haha"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "further_clarify_pre_error_haha": {
            "model_prompt": self_error_clarify, 
            "choices": {
                "Haha": "funny_pre_error",
                "That wasn't funny": "not_funny_pre_error"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_pre_error": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "fc_pre_error",
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_pre_error": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "fc_pre_error",
            },
            "protocols": {
                "continue": [],
            },
        },

        "fc_pre_error": {
            "model_prompt": [self_laughter_inform_eg, protocols_remind], 
            "choices": {
                "continue": "try_pre_protocol_neg_no_haha",
            },
            "protocols": {
                "continue": [],
            },
        },

        "further_clarify_pre_error_no_haha": {
            "model_prompt": [self_error_clarify, self_laughter_inform_eg, protocols_remind], 
            "choices": {
                "continue": "try_pre_protocol_neg_no_haha",
            },
            "protocols": {
                "continue": [],
            },
        },

        "explain_laughter_error": {
            "model_prompt": self_error_example,  
            "choices": {
                "continue": "continue_explaining_laughter_error",
            },
            "protocols": {
                "continue": [],
            },
        },

        "continue_explaining_laughter_error": {
            "model_prompt": [self_error_inform, feeling_pre_exercise_ask],
            "choices": {
                "\U0001F600": "continue_pos_pre_protocol_no_haha",
                "\U0001F641": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre_error(user_id)
            },
            "protocols": {
                "\U0001F600": [],
                "\U0001F641": [],
            }
        },

        "no_error_haha": {
            "model_prompt": [no_errors_respond],
            "choices": {
                "Haha": "funny_no_error",
                "That wasn't funny": "not_funny_no_error"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_no_error": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "ask_relevant_context"
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_no_error": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "ask_relevant_context"
            },
            "protocols": {
                "continue": [],
            },
        },

        "ask_relevant_context": {
            "model_prompt": more_relev_exercises_ask,
            "choices": {
                #can't do it
                "Yes": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_mini_session(user_id, "can't_do"), # TODO function that returns next prompt (random based on user's choice, emotion and current level)
                "No, I'd like to continue exploring errors": "continue_exploring_error"
            },
            "protocols": {
                "Yes": [],
                "No, I'd like to continue exploring errors": []
            },
        },

        "no_error_no_haha": {
            "model_prompt": [no_errors_respond, more_relev_exercises_ask],
            "choices": {
                #can't do it
                "Yes": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_mini_session(user_id, "can't_do"), # TODO function that returns next prompt (random based on user's choice, emotion and current level)
                "No, I'd like to continue exploring errors": "continue_exploring_error"
            },
            "protocols": {
                "Yes": [],
                "No, I'd like to continue exploring errors": []
            },
        },

        "continue_exploring_error": {
            "model_prompt": [self_error_encourage, feeling_pre_exercise_ask],
            "choices": {
                "\U0001F600": "continue_pos_pre_protocol_no_haha",
                "\U0001F641": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre_error(user_id)
            },
            "protocols": {
                "\U0001F600": [],
                "\U0001F641": [],
            }
        },

        # setbacks

        "ask_setback": {
            "model_prompt": setback_ask,
            "choices": {
                "yes": "ask_laughter_setback",
                "no": "empathetic_continue_curr_can't_do"
            },
            "protocols": {
                "yes": [decision_maker.PROTOCOL_TITLES[11]],
                "no": [decision_maker.PROTOCOL_TITLES[11]]
            },
        },

        "ask_laughter_setback": {
            "model_prompt": setback_laugh_ask,
            "choices": {
                "yes": "ask_feel_post_setback",
                "no": "ask_try_pre_setback"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "ask_feel_post_setback": {  
            "model_prompt": feeling_post_exercise_ask,
            "choices": {
                "Better": "try_post_protocol_pos",
                "No change": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_post_setback(user_id),
                "Worse": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_post_setback(user_id), #"post_setback_neg" #if already given contempt reminder otherwise, neg_repond, contempt, further_clar,
            },
            "protocols": {
                "Better": [],
                "No change": [],
                "Worse": [],
            },
        },

        "remind_contempt_post_setback": {
            "model_prompt": [neg_repond, not_contempt_note], 
            "choices": {
                "Sure": "ask_fc_post_setback", 
                "How can I stop this?": "how_not_contempt_post_setback",
            },
            "protocols": {
                "Sure": [],
                "How can I stop this?": []
            },
        },

        "ask_fc_post_setback": { 
            "model_prompt": further_clarification_ask,
            "choices": {
                "yes": "further_clarify_post_setback", 
                "no": "try_post_protocol_neg"
            }, 
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "further_clarify_post_setback": {
            "model_prompt": [laugh_setback_inform, protocols_remind, try_exercise_again_encourage],
            "choices": {
                "continue": "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        }, 

        "how_not_contempt_post_setback": {
            "model_prompt": [no_contempt_inform, further_clarification_ask], 
            "choices": {
                "yes": "further_clarify_post_setback", 
                "no": "try_post_protocol_neg" 
            }, 
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "post_setback_neg": {
            "model_prompt": [neg_repond, further_clarification_ask],
            "choices": {
                "yes": "further_clarify_post_setback",
                "no": "try_post_protocol_neg"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },            

        "ask_try_pre_setback": {
            "model_prompt": try_exercise_ask,
            "choices": {
                "Yes": "ask_setback_past",
                "No": "continue_curr_not_willing",
                "Not sure": "clarify_setback",
            },
            "protocols": {
                "Yes": [],
                "No": [],
                "Not sure": [],
            },
        },    

        "ask_setback_past": {
            "model_prompt": setback_distant_ask,
            "choices": {
                "yes": "remind_objectives_setback",
                "no": "propose_reflect_setback_haha",
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "remind_objectives_setback": {
            "model_prompt": [setback_laugh_inform, make_sense_ask],
            "choices": {
                "yes": "read_quote_setback",
                "no": "review_and_return_setback",
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "read_quote_setback": {
            "model_prompt": read_quote,
            "choices": {
                "continue": "give_quote_setback", 
            },
            "protocols": {
                "continue": [],
            },
        },

        "give_quote_setback": {
            "model_prompt": complete_quote_show,
            #TODO: check order!
            "choices": {
                "Done": "encourage_laughter_setback_haha", 
            },
            "protocols": {
                "Done": [],
            },
        },

        "encourage_laughter_setback_haha": {
            #TODO check encourage_setback_practice
            "model_prompt": laugh_setback_encourage,
            "choices": {
                "Haha": "funny_laugh_setback",
                "That wasn't funny": "not_funny_laugh_setback"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_laugh_setback": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "ask_pre_laughter_setback",
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_laugh_setback": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "ask_pre_laughter_setback",
            },
            "protocols": {
                "continue": [],
            },
        },

        "ask_pre_laughter_setback": {
            #TODO check encourage_setback_practice
            "model_prompt": feeling_pre_exercise_ask,
            "choices": {
                "\U0001F600": "continue_pos_pre_protocol_no_haha",
                "\U0001F641": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre_setback(user_id)#"pre_setback_neg"
            },
            "protocols": {
                "\U0001F600": [],
                "\U0001F641": [],
            }
        },

        "encourage_laughter_setback_no_haha": {
            #TODO check encourage_setback_practice
            "model_prompt": laugh_setback_encourage,
            "choices": {
                "continue": "ask_pre_laughter_setback",
            },
            "protocols": {
                "continue": [],
            }
        },

        "remind_contempt_pre_setback": {
            "model_prompt": not_contempt_note, 
            "choices": {
                "Sure": "pre_setback_neg", 
                "How can I stop this?": "how_not_contempt_pre_setback",
            },
            "protocols": {
                "Sure": [],
                "How can I stop this?": []
            },
        },

        "review_and_return_setback": {
            "model_prompt": needs_clarification_respond,
            "choices": {
                "continue": "encourage_laughter_setback_no_haha"
            },
            "protocols": {
                "continue": [],
            },
        },           
        
        "pre_setback_neg": {
            "model_prompt": further_clarification_ask,
            "choices": {
                "yes": "further_clarify_pre_setback",
                "no":  "try_pre_protocol_neg_no_haha"# or "continue_curr_not_willing"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "further_clarify_pre_setback": {
            "model_prompt": [laugh_setback_inform_eg, protocols_remind],
            "choices": {
                "continue": "try_pre_protocol_neg_no_haha"# or "continue_curr_not_willing",
            },
            "protocols": {
                "continue": [],
            },
        }, 

        "how_not_contempt_pre_setback": {
            "model_prompt": [no_contempt_inform, further_clarification_ask], 
            "choices": {
                "yes": "further_clarify_pre_setback", 
                "no": "try_pre_protocol_neg_no_haha" 
            }, 
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "propose_reflect_setback_haha": {
            "model_prompt": reflect_setback_encourage,
            "choices": {
                "Haha": "funny_setback",
                "That wasn't funny": "not_funny_setback"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_setback": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_can't_do",#lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre_setback(user_id),
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_setback": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_can't_do",#lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre_setback(user_id),
            },
            "protocols": {
                "continue": [],
            },
        },

        "propose_reflect_setback_no_haha": {
            "model_prompt": reflect_setback_encourage,
            "choices": {
                "continue": "continue_curr_can't_do",#lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre_setback(user_id),
            },
            "protocols": {
                "continue": [],
            },
        },

        "clarify_setback": {
            "model_prompt": [laugh_setback_clarify, try_exercise_ask],
            "choices": {
                "yes": "ask_setback_past",
                "no": "continue_curr_not_willing",
            },
            "protocols": {
                "yes": [],
                "no": [],
            },
        },     

        # hardships

        "ask_hardship": {
            "model_prompt": hardship_ask,
            "choices": {
                "Yes": "ask_accept_hardship_haha",
                "No": "empathetic_continue_curr_can't_do", 
                "Rather not say": "empathetic_response_hardship"
            },
            "protocols": {
                "Yes": [decision_maker.PROTOCOL_TITLES[12]],
                "No": [decision_maker.PROTOCOL_TITLES[12]],
                "Rather not say": [decision_maker.PROTOCOL_TITLES[12]]
            },
        },

        "ask_accept_hardship_haha": {
            "model_prompt": love_hardship_encourage,
            "choices": {
                "Haha": "funny_hardship",
                "That wasn't funny": "not_funny_hardship"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_hardship": {
            "model_prompt": [funny_respond, cont_hardship_ask],
            "choices": {
                "yes": "ask_feel_post_hardship",
                "no": "ask_try_pre_hardship", 
            },
            "protocols": {
                "yes": [],
                "no": [],
            },
        },

        "not_funny_hardship": {
            "model_prompt": [not_funny_respond, cont_hardship_ask],
            "choices": {
                "yes": "ask_feel_post_hardship",
                "no": "ask_try_pre_hardship", 
            },
            "protocols": {
                "yes": [],
                "no": [],
            },
        },

        "ask_accept_hardship_no_haha": {
            "model_prompt": love_hardship_encourage,
            "choices": {
                "yes": "ask_feel_post_hardship",
                "no": "ask_try_pre_hardship", 
            },
            "protocols": {
                "yes": [],
                "no": [],
            },
        },

        "ask_feel_post_hardship": {
            "model_prompt": feeling_post_exercise_ask,
            "choices": {
                "Better": "try_post_protocol_pos",
                "No change": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_post_hardship(user_id),
                "Worse": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_post_hardship(user_id),
            },
            "protocols": {
                "Better": [],
                "No change": [],
                "Worse": [],
            },
        },

        "remind_contempt_post_hardship": {
            "model_prompt": [neg_repond, not_contempt_note], 
            "choices": {
                "Sure": "further_clarify_post_hardship", 
                "How can I stop this?": "how_not_contempt_post_hardship",
            },
            "protocols": {
                "Sure": [],
                "How can I stop this?": []
            },
        },

        "further_clarify_post_hardship": {
            "model_prompt": [laugh_hardship_inform, protocols_remind],
            "choices": {
                "continue": "try_post_protocol_neg",
            },
            "protocols": {
                "continue": [],
            },
        },

        "how_not_contempt_post_hardship": {
            "model_prompt": [no_contempt_inform, further_clarification_ask], 
            "choices": {
                "yes": "further_clarify_post_hardship", 
                "no": "try_post_protocol_neg" 
            }, 
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "post_hardship_neg": {
            "model_prompt": [neg_repond, further_clarification_ask],
            "choices": {
                "yes": "further_clarify_post_hardship",
                "no": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_post(user_id) 
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "ask_try_pre_hardship": {
            "model_prompt": try_exercise_ask, 
            "choices": {
                "Yes": "ask_hardship_past",
                "No": "continue_curr_not_willing", 
                "Not sure": "clarify_hardship",
            },
            "protocols": {
                "Yes": [],
                "No": [],
                "Not sure": []
            },
        },

        "ask_hardship_past": {
            "model_prompt": hardship_past_ask,
            "choices": {
                "yes": "remind_objectives_hardship",
                "no": "propose_reflect_hardship_haha",
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "remind_objectives_hardship": {
            "model_prompt": [hardship_laugh_inform, make_sense_ask],
            "choices": {
                "yes": "read_quote_hardship",
                "no": "review_and_return_hardship",
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "read_quote_hardship": {
            "model_prompt": read_quote,
            "choices": {
                "continue": "give_quote_hardship", 
            },
            "protocols": {
                "continue": [],
            },
        },

        "give_quote_hardship": {
            "model_prompt": complete_quote_show,
            #TODO: check order!
            "choices": {
                "Done": "encourage_laughter_hardship_no_haha", 
            },
            "protocols": {
                "Done": [],
            },
        },

        "review_and_return_hardship": {
            "model_prompt": needs_clarification_respond,
            "choices": {
                "continue": "encourage_laughter_hardship_no_haha"
            },
            "protocols": {
                "continue": [],
            },
        },

        "encourage_laughter_hardship_haha": {
            "model_prompt": laugh_hardship_encourage,
            "choices": {
                "Haha": "funny_hardship_practice",
                "That wasn't funny": "not_funny_hardship_practice"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },

        "funny_hardship_practice": {
            # should we have variety or do similar to setbacks - continue to break up 
            "model_prompt": [funny_respond, feeling_pre_exercise_ask],
            "choices": {
                "continue": "ask_pre_hardship_practice", 
            },
            "protocols": {
                "continue": [],
            }
        },

        "not_funny_hardship_practice": {
            "model_prompt": [not_funny_respond, feeling_pre_exercise_ask],
            "choices": {
                "continue": "ask_pre_hardship_practice", 
            },
            "protocols": {
                "continue": [],
            }
        },

        "encourage_laughter_hardship_no_haha": {
            "model_prompt": laugh_hardship_encourage,
            "choices": {
                "continue": "ask_pre_hardship_practice", 
            },
            "protocols": {
                "continue": [],
            }
        },

        "ask_pre_hardship_practice": {
            "model_prompt": feeling_pre_exercise_ask,
            "choices": {
                "\U0001F600": "continue_pos_pre_protocol_no_haha", 
                "\U0001F610": "pre_hardship_neg",
                "\U0001F641": lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre_hardship(user_id), 
            },
            "protocols": {
                "\U0001F600": [],
                "\U0001F610": [],
                "\U0001F641": [],
            }
        },

        "remind_contempt_pre_hardship": {
            "model_prompt": not_contempt_note, 
            "choices": {
                "Sure": "pre_hardship_neg", 
                "How can I stop this?": "how_not_contempt_pre_hardship",
            },
            "protocols": {
                "Sure": [],
                "How can I stop this?": []
            },
        },

        "pre_hardship_neg": {
            "model_prompt": further_clarification_ask,
            "choices": {
                "yes": "further_clarify_pre_hardship",
                "no": "try_pre_protocol_neg_no_haha" # or "continue_curr_not_willing",
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "how_not_contempt_pre_hardship": {
            "model_prompt": [no_contempt_inform, further_clarification_ask], 
            "choices": {
                "yes": "further_clarify_pre_hardship", 
                "no": "try_pre_protocol_neg_no_haha" 
            }, 
            "protocols": {
                "yes": [],
                "no": []
            },
        },

        "further_clarify_pre_hardship": {
            #TODO check this
            "model_prompt": [laugh_hardship_inform, protocols_remind],
            "choices": {
                "continue": "try_pre_protocol_neg_no_haha",
            },
            "protocols": {
                "continue": [],
            },
        }, 

        "propose_reflect_hardship_haha": {
            "model_prompt": reflect_hardship_encourage,
            "choices": {
                "Haha": "funny_hardship_reflect",
                "That wasn't funny": "not_funny_hardship_reflect"
            },
            "protocols": {
                "Haha": [],
                "That wasn't funny": []
            },
        },
        
        "funny_hardship_reflect": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_can't_do",#lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre_setback(user_id),
            },
            "protocols": {
                "continue": [],
            },
        },

        "not_funny_hardship_reflect": {
            "model_prompt": lambda user_id, db_session, curr_session, app: get_model_prompt_not_funny_respond(decision_maker, user_id),
            "choices": {
                "continue": "continue_curr_can't_do",#lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre_setback(user_id),
            },
            "protocols": {
                "continue": [],
            },
        },

        "propose_reflect_hardship_no_haha": {
            "model_prompt": reflect_hardship_encourage,
            "choices": {
                "continue": "continue_curr_can't_do",#lambda user_id, db_session, curr_session, app: decision_maker.check_contempt_pre_setback(user_id),
            },
            "protocols": {
                "continue": [],
            },
        },

        "clarify_hardship": {
            "model_prompt": [laugh_hardship_clarify, try_exercise_ask],
            #TODO: do we want a pause or a continue before asking want to try?
            "choices": {
                "yes": "ask_hardship_past",
                "no": "continue_curr_not_willing", 
            },
            "protocols": {
                "yes": [],
                "no": [],
            },
        },

        "empathetic_response_hardship": {
            "model_prompt": [not_share_respond, more_exercises_ask],
            "choices": {
                #negative/rather not
                "yes": lambda user_id, db_session, curr_session, app: decision_maker.determine_next_mini_session(user_id, "not_willing"),
                "no": "review_any_session"
            },
            "protocols": {
                "yes": [],
                "no": []
            },
        },
    }

    return QUESTIONS