import string
import nltk

from model.models import UserModelSession, Choice, UserModelRun, Protocol
from model.classifiers import get_emotion, get_sentence_score
from model.utterances import *
import pandas as pd
import numpy as np
import random
from collections import deque
import re
import datetime
import time

nltk.download("wordnet")
from nltk.corpus import wordnet  # noqa

class ModelDecisionMaker:
    def __init__(self):

        # removed personas
        self.kai = pd.read_csv('/Users/zeenapatel/dev/HumBERT/model/kai.csv', encoding='ISO-8859-1') # changed path
        
        self.PROTOCOL_TITLES = [
            "0: None",
            "1: Playful mind",
            "2: Playful face",
            "3: Self-glory",
            "4: Incongruous world",
            "5: Incongruous self",
            "6: Self/world incongruity",
            "7: Contrasting views",
            "8: Our own laughter brand",
            "9: Feigning laughter",
            "10: Self-laughter",
            "11: Laughing at misfortunes and disturbing circumstances",
            "12: Laughing at long-term suffering",
        ]

        self.TITLE_TO_PROTOCOL = {
            # "Playful mind" (protocol 1) maps to 1
            self.PROTOCOL_TITLES[i]: i for i in range(len(self.PROTOCOL_TITLES))
        }

        # map each protocol to a 'difficulty level' to help determine which protocol the chatbot should recommend
        self.PROTOCOL_TO_LEVEL = dict(zip(self.PROTOCOL_TITLES, [0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 3, 3]))

        self.TINY_SESSION_TITLES = [
            ("1: Playful mind", "2: Playful face"), 
            ("3: Self-glory",), 
            ("4: Incongruous world", "5: Incongruous self", "6: Self/world incongruity"), 
            ("7: Contrasting views",), 
            ("8: Our own laughter brand", "9: Feigning laughter"), 
            ("10: Self-laughter",), 
            ("11: Laughing at misfortunes and disturbing circumstances",), 
            ("12: Laughing at long-term suffering",)
        ]

        self.TINY_SESSION_TITLE_TO_LEVEL = dict(zip(self.TINY_SESSION_TITLES, [0, 0, 1, 1, 1, 2, 3, 3]))

        self.TINY_SESSION_QUESTIONS = ["ask_playful_mode", "ask_self_glory", "ask_incongruity", "ask_feel_pre_cv", "ask_laughter_brand", "ask_recent_error", "ask_setback", "ask_hardship"]

        self.TINY_SESSION_TO_QUESTION = dict(zip(self.TINY_SESSION_TITLES, self.TINY_SESSION_QUESTIONS))
        self.QUESTION_TO_TINY_SESSION = dict(zip(self.TINY_SESSION_QUESTIONS, self.TINY_SESSION_TITLES))

        #TODO: check if we need self.NEGATIVE_TINY_SESSION_TITLES, QUESTIONS, self.PROTOCOL_MINI_SESSIONS,etc.

        self.NEGATIVE_TINY_SESSION_TITLES = [
            ("4: Incongruous world", "5: Incongruous self", "6: Self/world incongruity"), 
            ("10: Self-laughter",), 
            ("11: Laughing at misfortunes and disturbing circumstances",), 
            ("12: Laughing at long-term suffering",)
        ]
        self.NEGATIVE_TINY_SESSION_TITLE_TO_LEVEL = dict(zip(self.NEGATIVE_TINY_SESSION_TITLES, [1, 2, 3, 3]))
        self.NEGATIVE_TINY_SESSION_QUESTIONS = ["ask_laughter_incongruity", "ask_feel_pre_error", "ask_laughter_setback", "ask_accept_hardship"]
        self.NEGATIVE_TINY_SESSION_TO_QUESTION = dict(zip(self.NEGATIVE_TINY_SESSION_TITLES, self.NEGATIVE_TINY_SESSION_QUESTIONS))
        self.QUESTION_TO_NEGATIVE_TINY_SESSION = dict(zip(self.NEGATIVE_TINY_SESSION_QUESTIONS, self.NEGATIVE_TINY_SESSION_TITLES))

        
        # Stores the initial emotional state of each user after they classify it (positive or negative)
        self.user_states_initial = {}
        # Tracks the current emotional state of each user (positive or negative)
        self.user_states = {}
        # Tracks the feeling of each user before or aftter attempting the current protocol (positive & negative or better, worse & same)
        # keys: user ids, values: string tuples: (pre/post, feeling)
        self.user_protocol_feelings = {}
        # Tracks each user's current tiny session (including None)
        self.user_tiny_sessions = {}
        # Tracks the tiny sessions covered by each user so far 
        self.user_covered_sessions = {}

        self.recent_protocols = deque(maxlen=12)
        self.reordered_protocol_questions = {}
        self.protocols_to_suggest = []

        # Goes from user id to actual value
        self.current_run_ids = {}
        self.current_protocol_ids = {}

        self.current_protocols = {}

        self.positive_protocols = [i for i in range(1, 13)]

        # Keys: user ids, values: dictionaries describing each choice (in list)
        # and current choice
        self.user_choices = {}

        # Keys: user ids, values: scores for each question
        #self.user_scores = {}

        # Keys: user ids, values: current suggested protocols
        self.suggestions = {}

        # Tracks current emotion of each user after they classify it
        self.user_emotions = {}

        # Tracks whether each user has received the contempt message 
        self.contempt_message = {}
        
        self.guess_emotion_predictions = {}

        self.users_names = {}
        self.remaining_choices = {}

        self.recent_questions = {}

        self.chosen_personas = {}
        self.datasets = {}

        # Structure of dictionary: {question: {
        #                           model_prompt: str or list[str],
        #                           choices: {maps user response to next protocol},
        #                           protocols: {maps user response to protocols to suggest},
        #                           }, ...
        #                           }
        # This could be adapted to be part of a JSON file (would need to address
        # mapping callable functions over for parsing).
        self.QUESTIONS = {

            #################### MAIN SESSION ####################

            "ask_name": {
               "model_prompt": "Hi! I\'m Humbert, a self-employed laughter assistant. May I know your name?",
               "choices": {
                   "open_text": lambda user_id, db_session, curr_session, app: self.save_name(user_id)
               },
               "protocols": {"open_text": []},
           },

            "opening_prompt": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_opening_prompt(user_id),
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
                "model_prompt": "Great. Just to let you know, they are also being displayed on the right if you wish to review them at any point in our conversation.",
                "choices": {
                    "continue": "constant_practice",
                },
                "protocols": {
                    "continue": []
                },
            }, 

            "constant_practice": {
                "model_prompt": ["We will be discussing some of these today, but practising these during your daily life is where you will receive the real benefit as your laughter will become more natural and frequent, and you\'ll feel happier for it.", 
                "Practice makes perfect. And I make comedians! Ok, that may not be completely true; but we can take it in steps!"],
                "choices": {
                    "Haha": "constant_practice_funny",
                    "That wasn't funny": "constant_practice_not_funny"
                },
                "protocols": {
                    "Haha": [],
                    "That wasn't funny": [],
                },
            },

            "recommend_review": {
                "model_prompt": ["I would recommend reviewing these briefly before we talk as you can use this session to consolidate your understanding of them.", 
                "They are being displayed on the right if you wish to review them now or at any point in our conversation."],
                "choices": {
                    "continue": "constant_practice",
                },
                "protocols": {
                    "continue": []
                },
            }, 

            "constant_practice_funny": {
                "model_prompt": "I\'m glad you found that funny. I\'ve also been trying to develop my sense of humour!",
                "choices": {
                    "continue": "get_started",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "constant_practice_not_funny": {
                "model_prompt": "You\'re hard to impress. I\'ll try harder next time!",
                "choices": {
                    "continue": "get_started",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "get_started": {
                "model_prompt": ["Just to let you know, our conversation might include some humour jargon. But don\'t worry, I\'ll identify this with CAPITALS, and you can ask me for clarification or look it up in the documentation in your own time.", 
                "Anyway, enough with the intros - we can start whenever you're ready!"],
                "choices": {
                    "Let's start": "ask_emotion",
                },
                "protocols": {
                    "Let's start": []
                },
            }, 

            "ask_emotion": {
               "model_prompt": "How are you feeling today? Try to be honest; I will not judge you!", 
               "choices": {
                    "open_text": lambda user_id, db_session, curr_session, app: self.determine_next_prompt_start_session(user_id, app, db_session)
                },
                "protocols": {"open_text": []},
           },

            "guess_emotion": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_guess_emotion(
                    user_id, app, db_session
                ),
                "choices": {
                    "yes": {
                        "Sad": "after_classification_negative", # changed all from negative for initial rule-based implementation
                        "Angry": "after_classification_negative",
                        "Anxious/Scared": "after_classification_negative",
                        "Happy/Content": "after_classification_positive", # changed from positive for initial rule-based implementation
                    },
                    "no": "check_emotion",
                },
                "protocols": {
                    "yes": [],
                    "no": [],
                    },
            },

            "check_emotion": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_check_emotion(user_id, app, db_session),

                "choices": {
                    "Sad": lambda user_id, db_session, curr_session, app: self.get_sad_emotion(user_id),
                    "Angry": lambda user_id, db_session, curr_session, app: self.get_angry_emotion(user_id),
                    "Anxious/Scared": lambda user_id, db_session, curr_session, app: self.get_anxious_emotion(user_id),
                    "Happy/Content": lambda user_id, db_session, curr_session, app: self.get_happy_emotion(user_id),
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
                "model_prompt": "Great! Let\'s start exploring how to develop your sense of humour.",

                "choices": {
                    "continue": lambda user_id, db_session, curr_session, app: self.determine_first_mini_session(),
                },
                "protocols": {
                    "continue": [], 
                },
            },

            # start negative session
            # conversation redirects to MAIN SESSION (NEGATIVE)
            "after_classification_negative": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_opening_prompt_negative(user_id),
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

            # main session covered all 12 protocols (in tiny/mini sessions)
            "covered_all_sessions": {
                "model_prompt": "We have now covered all the relevant contexts for humour. Congratulations! Are there any specific protocols that you'd like to review?",
                "choices": {
                    "Yes": "choose_any",
                    "No (end session)": lambda user_id, db_session, curr_session, app: self.end_session(user_id)
                },
                "protocols": {
                    "Yes": [],
                    "No (end session)": []
                },
            },

            "review_any_session": {
                "model_prompt": "Before we end our conversation, are there any specific protocols that you'd like to review?",
                "choices": {
                    "Yes": "choose_any",
                    "No (end session)": lambda user_id, db_session, curr_session, app: self.end_session(user_id)
                },
                "protocols": {
                    "Yes": [],
                    "No (end session)": []
                },
            },

            "choose_any": {
                "model_prompt": "Please select the protocol you wish to review?",
                "choices": {
                    "Playful mode": "ask_playful_mode",
                    "Self-glory": "ask_acknowledge_achievements",
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
                "model_prompt": ["That ends our session then!", ask_present_feeling],
                "choices": {
                    "Better": "ending_better",
                    "Worse": "ending_neg",
                    "No change": "ending_neg",
                },
                "protocols": {
                    "Better": [],
                    "Worse": [],
                    "No change": [],
                },
            },

            "ending_better": {
                "model_prompt": [empathetic_response_pos, "It would be most beneficial if you could recognise the discussed contexts for laughter (i.e. self and or world incongruity, error/fault, daily routine-accomplishment, etc.) as often as possible throughout your life.", 
                "There is no endpoint to developing a sense of humour, it is a journey, and the most important thing is to enjoy it!", 
                "And I am always here if you need me – I have nowhere else to go!"],
                "choices": {
                    "Goodbye": "ending_message",
                    "I'd like to have another session": "another_session",
                },
                "protocols": {
                    "Goodbye": [],
                    "I'd like to have another session": [],
                },
            },

            "ending_neg": {
                "model_prompt": [empathetic_response_neg, "It would be most beneficial if you could recognise the discussed contexts for laughter (i.e. self and or world incongruity, error/fault, daily routine-accomplishment, etc.) as often as possible throughout your life.", 
                "There is no endpoint to developing a sense of humour, it is a journey, and the most important thing is to enjoy it!", 
                "And I am always here if you need me – I have nowhere else to go!"],
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
                "model_prompt": ["It would be most beneficial if you could recognise the discussed contexts for laughter (i.e. self and or world incongruity, error/fault, daily routine-accomplishment, etc.) as often as possible throughout your life.", 
                "There is no endpoint to developing a sense of humour, it is a journey, and the most important thing is to enjoy it!", 
                "And I am always here if you need me – I have nowhere else to go!"],
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
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_ending_message(user_id),
                "choices": {},
                "protocols": {},
            },

            "another_session": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.want_another_session(user_id),
                "choices": {},
                "protocols": {},
            },

            #################### REUSED PARTS OF CONVERSATION ####################
            
            # continue exploring

            "continue_curr_can't_do": {
                "model_prompt": continue_other,
                "choices": {
                    "yes": lambda user_id, db_session, curr_session, app: self.determine_next_tiny_session(user_id, "can't_do"), # function that returns next prompt (random based on user's choice, emotion and current level)
                    "no": "review_any_session",#"lambda user_id, db_session, curr_session, app: self.end_session(user_id)"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "empathetic_continue_curr_can't_do": {
                "model_prompt": [empathetic_response_pos, continue_other],
                "choices": {
                    "yes": lambda user_id, db_session, curr_session, app: self.determine_next_tiny_session(user_id, "can't_do"), # function that returns next prompt (random based on user's choice, emotion and current level)
                    "no": "review_any_session" #lambda user_id, db_session, curr_session, app: self.end_session(user_id)
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "continue_curr_not_willing": {
                "model_prompt": continue_other,
                "choices": {
                    "yes": lambda user_id, db_session, curr_session, app: self.determine_next_tiny_session(user_id, "not_willing"), # function that returns next prompt (random based on user's choice, emotion and current level)
                    "no": "review_any_session"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "continue_curr_willing": {
                "model_prompt": continue_other,
                "choices": {
                    "yes": lambda user_id, db_session, curr_session, app: self.determine_next_tiny_session(user_id, "willing"), # function that returns next prompt (random based on user's choice, emotion and current level)
                    "no": "review_any_session"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "continue_pos_pre_protocol": {
                "model_prompt": [empathetic_resp_pos_pre, continue_other], 
                "choices": {
                    "yes": lambda user_id, db_session, curr_session, app: self.determine_next_tiny_session(user_id, "willing"), # function that returns next prompt (random based on user's choice, emotion and current level)
                    "no": "review_any_session"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            # encourage practice

            "try_pre_protocol_pos": {
                "model_prompt": [empathetic_response_pos, try_this], 
                "choices": {
                    "continue": "continue_curr_willing"
                },
                "protocols": {
                    "continue": [],
                },
            },

            "try_pre_protocol_neg": {
                "model_prompt": try_this,
                "choices": {
                    "continue": "continue_curr_not_willing",
                },
                "protocols": {
                    "continue": [],
                },
            }, 

            "try_pre_protocol_neg_no_contempt":{
                "model_prompt": [how_not_contempt, try_this],
                "choices": {
                    "continue": "continue_curr_not_willing",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "try_laughter_pre_protocol_pos": {
                "model_prompt": try_this,
                "choices": {
                    "continue": "continue_curr_willing",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "try_post_protocol_pos": {
                "model_prompt": [empathetic_response_pos, try_this_again], 
                "choices": {
                    "continue": "continue_curr_willing"                },
                "protocols": {
                    "continue": [],
                },
            },

            "try_post_protocol_neg":{
                "model_prompt": try_this_again, 
                "choices": {
                    "continue": "continue_curr_not_willing",
                },
                "protocols": {
                    "continue": [],
                },
            },

            # more explanation
            "review_post_protocol_neg": {
                "model_prompt": [empathetic_response_neg, look_at_sheet],
                "choices": {
                    "continue": "try_post_protocol_neg", 
                },
                "protocols": {
                    "continue": [],
                },
            },

            # no contempt 

            "remind_contempt_post_protocol":{
                "model_prompt": not_contempt, 
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
                "model_prompt": [how_not_contempt, try_this_again], 
                "choices": {
                    "continue": "continue_curr_not_willing",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "remind_contempt_pre_protocol":{
                "model_prompt": not_contempt, 
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
                "model_prompt": how_not_contempt, 
                "choices": {
                    "continue": "continue_curr_not_willing",
                },
                "protocols": {
                    "continue": [],
                },
            },

            #################### TINY SESSIONS ####################

            # playful mode

            "ask_playful_mode": {
                "model_prompt": "Is your body in a playful mode?",
                "choices": {
                    "yes": "ask_acknowledge_achievements",
                    "no": "inform_playful"
                },
                "protocols": {
                    "yes": [self.PROTOCOL_TITLES[1], self.PROTOCOL_TITLES[2]],
                    "no": [self.PROTOCOL_TITLES[1], self.PROTOCOL_TITLES[2]]
                },
            },

             "ask_acknowledge_achievements": {
                "model_prompt": [empathetic_response_pos, "As adults, we sometimes get stuck in a serious mode!"],
                #TODO: should we have choices: haha & not funny
                "choices": {
                    "continue": lambda user_id, db_session, curr_session, app: self.check_acknowledge_achievements(user_id),
                },
                "protocols": {
                    "continue": [self.PROTOCOL_TITLES[1], self.PROTOCOL_TITLES[2]],
                },
            },

            "inform_playful": {
                "model_prompt": "A useful skill for developing your sense of humour is to become more flexible and playful about your thoughts and beliefs.",
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
                "model_prompt": "Let\'s explore another way to get into a playful mode.",
                "choices": {
                    "continue": "ask_song",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "ask_song":{
                # TODO: should we add a delay
                "model_prompt": "Do you have a favourite song?",
                "choices": {
                    "yes": "response_to_song",
                    "no": "recommend_song"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "response_to_song": {
                "model_prompt": "Great, I won\'t make you share it as I know that can be very personal.",
                "choices": {
                    "continue": "recommend_playful_protocol",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "recommend_playful_protocol": {
                "model_prompt": ["Another way to become more playful is to loosen up your mouth and eye muscles by moving them around and singing your chosen song.", 
                ask_pre_protocol_feeling],
                "choices": {
                    "Positive": "continue_pos_pre_protocol",
                    "Negative": "pre_playful_neg"
                },
                "protocols": {
                    "Positive": [],
                    "Negative": [],
                },
            },

            "recommend_song": {
                "model_prompt": "How about {}? Or even make up your own!",
                "choices": {
                    "continue": "recommend_playful_protocol",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "pre_playful_neg": {
                "model_prompt": [look_at_sheet, try_this],
                "choices": {
                    "continue": "continue_curr_not_willing",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "example_playful": {
                "model_prompt": ["You could explore counterpositions to a strongly followed belief.",
                "For example, employees are happier and therefore more productive in clothes they feel comfortable in, so I believe everyone should be allowed to turn up to work in their pyjamas!",
                try_this],
                "choices": {
                    "continue": "explore_playful"
                },
                "protocols": {
                    "continue": []
                },
            },

            # self-glory

            "ask_self_glory": {
                "model_prompt": "Do you spend any time acknowledging your simple achievements, such as daily routine tasks?",
                "choices": {
                    "yes": "ask_congratulate_with_smile",
                    "no": "propose_congratulate_with_smile"
                },
                "protocols": {
                    "yes": [self.PROTOCOL_TITLES[3]],
                    "no": [self.PROTOCOL_TITLES[3]]
                },
            },

            "ask_congratulate_with_smile": {
                "model_prompt": "Have you tried congratulating yourself on these achievements with a laugh or smile?",
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
                "model_prompt": ask_post_protocol_feeling,
                "choices": {
                    "Better": "try_post_protocol_pos", 
                    "Worse": "review_post_protocol_neg",
                    "No change": "review_post_protocol_neg",
                },
                "protocols": {
                    "Better": [],
                    "Worse": [],
                    "No change": [],
                },
            },
            
            "propose_sg_and_eg": {
                "model_prompt": "How would you feel about trying this on your own, over simple things, like brushing your teeth?",
                "choices": {
                    "Positive": "continue_pos_pre_protocol", 
                    "Negative": "pre_sg_neg"
                },
                "protocols": {
                    "Positive": [],
                    "Negative": []
                },
            },

            "pre_sg_neg": {
                # TODO: do we want empathetic_response_neg?
                "model_prompt": [empathetic_response_neg, further_clarification],
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
                "model_prompt": [incongruity_and_superiority, look_at_sheet],
                "choices": {
                    "continue": "continue_curr_not_willing"
                },
                "protocols": {
                    "continue": [],
                },
            },

            "propose_congratulate_with_smile": {
                "model_prompt": ["Try congratulating yourself, via a smile or laugh, on something simple that you have completed, such as doing the dishes or even the act of breathing!"],
                "choices": {
                    "continue": "continue_curr_can't_do"
                },
                "protocols": {
                    "continue": [],
                },
            },

            # incongruity

            "ask_incongruity": {
                "model_prompt": "Have you experienced any incongruity in your life lately?",
                "choices": {
                    "Yes": "ask_laughter_incongruity",
                    "No": "no_incongruity",
                    "Not sure": "reminder_incongruity",
                },
                "protocols": {
                    "Yes": [self.PROTOCOL_TITLES[4], self.PROTOCOL_TITLES[5], self.PROTOCOL_TITLES[6]],
                    "No": [self.PROTOCOL_TITLES[4], self.PROTOCOL_TITLES[5], self.PROTOCOL_TITLES[6]], 
                    "Not sure": [self.PROTOCOL_TITLES[4], self.PROTOCOL_TITLES[5], self.PROTOCOL_TITLES[6]]
                },
            },

            "ask_laughter_incongruity": {
                "model_prompt": ask_pre_protocol_feeling_laughter, # are you able to laugh this off
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
                "model_prompt": further_clarification,
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
                "model_prompt": ["Incongruity can be a trigger for true (Duchenne) laughter.",
                "You might have experienced this through any changes in the outside world or your own contradictions or change of attitudes.",
                "On the other hand, it could be an inconsistency between the reality of the external world and our expectations.", 
                look_at_sheet],
                "choices": {
                    "continue": "try_laughter_incongruity",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "try_laughter_incongruity": {
                "model_prompt": "If you\'re feeling up to it, try laughing at this incongruity on your own.", # how does that sound? + -> great - come back tell me
                "choices": {
                    "continue": "ask_feel_pre_incongruity", 
                },
                "protocols": {
                    "continue": [],
                },
            },

            "ask_feel_pre_incongruity": {
                "model_prompt": ask_pre_protocol_feeling,
                "choices": {
                    "Positive": "continue_pos_pre_protocol",
                    "Negative": lambda user_id, db_session, curr_session, app: self.check_contempt_pre(user_id),
                    "Neutral": "continue_curr_not_willing",
                },
                "protocols": {
                    "Positive": [],
                    "Negative": [],
                    "Neutral": [],
                },
            },

            "no_incongruity": {
                "model_prompt": ["I see. I hope you're not finding it too boring then!", continue_other],
                "choices": {
                    "yes": lambda user_id, db_session, curr_session, app: self.determine_next_tiny_session(user_id, "can't_do"), # function that returns next prompt (random based on user's choice, emotion and current level)
                    "no": "review_any_session"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },          

            "reminder_incongruity": {
                "model_prompt": ["No problem - there are lots of terms associated with humour, as I'm sure you'ved realised!",
                "An incongruity is an inconsistency or discrepancy that can usually be in the outside world or your own life, mind and behaviours.",
                "It could even be a contrast between world realities compared to our expectations.",
                ],
                "choices": {
                    "I see": "ask_incongruity_no_unsure",
                    "Can I have an example": "example_incongruity",
                },
                "protocols": {
                    "I see": [],
                    "Can I have an example": [],
                },
            },

            "ask_incongruity_no_unsure": {
                "model_prompt": "Have you experienced any incongruity in your life lately?",
                "choices": {
                    "yes": "ask_laughter_incongruity",
                    "no": "continue_curr_can't_do",
                },
                "protocols": {
                    "yes": [],
                    "no": [], 
                },
            },

            "example_incongruity": {
                "model_prompt": "One example I can think of is when I caught my grandma riding my bike last week - that was quite bizarre!",
                "choices": {
                    "continue": "ask_incongruity_no_unsure",
                },
                "protocols": {
                    "continue": [],
                },
            },

            # contrasting views

            "ask_feel_pre_cv": {
                "model_prompt": "How do you feel about the idea of exploiting a change in your perception of an image as a trigger for laughter?",
                "choices": {
                    "Sounds interesting": "pre_cv_pos", 
                    "What?": "pre_cv_neg"
                },
                "protocols": {
                    "Sounds interesting": [self.PROTOCOL_TITLES[7]],
                    "What?": [self.PROTOCOL_TITLES[7]]
                },
            },

            "pre_cv_pos": {
                "model_prompt": [empathetic_response_pos, further_clarification], 
                "choices": {
                    "yes": "further_clarify_cv", 
                    "no": "try_laughter_pre_protocol_pos",
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "further_clarify_cv": {
                #TODO: should we perform a search?
                "model_prompt": ["You can induce a change in perception by staring at the image of this Gestalt vase where you should also see two white faces and smile or laugh while repetitively switching between both interpretations.", 
                "It sounds fancy, right? It comes from Gestalt psychology.", # extension - wiki search if user would like to know more
                ],
                "choices": {
                    "Sounds interesting": "try_pre_protocol_neg",
                    "What?": "explain_cv",
                },
                "protocols": {
                    "Sounds interesting": [],
                    "What?": [],
                },
            },

            "explain_cv": {
                #TODO: should we perform a search?
                "model_prompt": [look_at_sheet, try_this],
                "choices": {
                    "continue": "continue_curr_can't_do",
                },
                "protocols": {
                    "continue": [],
                },
            },    

            "pre_cv_neg": {
                #TODO
                "model_prompt": further_clarification,
                "choices": {
                    "yes": "further_clarify_cv",
                    "no": "try_pre_protocol_neg",
                },
                "protocols": {
                    "yes": [],
                    "no": [], 
                },
            },    

            # own laughter brand

            "ask_laughter_brand": {
                "model_prompt": "Have you tried producing new forms of laughter?",
                "choices": {
                    "yes": "ask_feel_post_lb",
                    "no": "explain_lb"
                },
                "protocols": {
                    "yes": [self.PROTOCOL_TITLES[8], self.PROTOCOL_TITLES[9]],
                    "no": [self.PROTOCOL_TITLES[8], self.PROTOCOL_TITLES[9]]
                },
            },

            "ask_feel_post_lb": {
                "model_prompt": ask_post_protocol_feeling,
                "choices": {
                    "Better": "post_lb_pos",
                    "Worse": "post_lb_neg",
                    "No change": "post_lb_neg",
                },
                "protocols": {
                    "Better": [],
                    "Worse": [],
                    "No change": [],
                },
            },

            "post_lb_pos": {
                "model_prompt": [empathetic_response_pos, encourage_own_laughter],
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
                "model_prompt": ["Another related exercise often practised in laughter yoga is feigning Duchenne laughter.",
                "You could try this in your own time as a mental exercise to keep your spirits high.", ask_pre_protocol_feeling],
                "choices": {
                    "Positive": "continue_pos_pre_protocol",
                    "Negative": "pre_fl_neg",
                },
                "protocols": {
                    "Positive": [],
                    "Negative": [],
                },
            },

            "pre_fl_neg": {
                # TODO: wording change? Perhaps some further clarification might help?
                "model_prompt": [empathetic_response_neg, further_clarification],
                "choices": {
                    "yes": "further_clarify_fl",
                    "no": "continue_curr_not_willing"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "further_clarify_fl": {
                "model_prompt": ["Duchenne laughter is considered the sole indicator of true enjoyment.",
                "Just as we practice swimming or running as a physical exercise rather than trying to get from A to B, we practice feigning laughter (laughing without humour) to exercise our minds.", 
                look_at_sheet],
                "choices": {
                    "continue": "continue_curr_not_willing",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "post_lb_neg": {
                "model_prompt": [empathetic_response_neg, "Creating your own form of laughter can be very beneficial to your general mood and when trying to cope with stress.",
                "But it does take time to perfect, so don\'t feel you need to rush it!"],
                "choices": {
                    "continue": "ask_explore_related",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "explain_lb": {
                "model_prompt": ["Then this should be fun! To playfully create your form of laughter, perform the following:", 
                "loosen the muscles around your mouth and keep your mouth open while repeating one of the following repetitious phrases (using any vowel) and turning it into laughter:", 
                "ah, ah, ah, ah, eh, eh, eh, eh, oh, oh, oh, oh, ih, ih, ih, ih, ih, uh, uh, uh, uh, ..."],
                "choices": {
                    "continue": "continue_explaining_lb",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "continue_explaining_lb": {
                "model_prompt": ["Try to ensure that your form of laughter requires a minimum amount of energy (so you can use it for extended periods).",
                make_sense],
                "choices": {
                    "yes": "try_pre_lb",
                    "no": "further_clarify_lb"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "try_pre_lb": {
                "model_prompt": [empathetic_response_pos, encourage_own_laughter, 
                "Maybe don\'t try this at the zoo, though, as they might not let you out!"],
                "choices": {
                    "Haha": "funny_lb",
                    "That wasn't funny": "not_funny_lb"
                },
                "protocols": {
                    "Haha": [],
                    "That wasn't funny": []
                },
            },

            "further_clarify_lb": {
                "model_prompt": look_at_sheet,
                "choices": {
                    "continue": "encourage_try_lb",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "encourage_try_lb": {
                "model_prompt": [encourage_own_laughter, 
                "Maybe don\'t try this at the zoo, though, as they might not let you out!"],
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
                "model_prompt": ["I\'m glad you found that funny. I\'ve also been trying to develop my sense of humour!", 
                "Would you like to explore a related exercise?"],
                "choices": {
                    "yes": "ask_feigning_laughter",
                    "no": "continue_curr_not_willing"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "not_funny_lb": {
                "model_prompt": ["You\'re hard to impress. I\'ll try harder next time!", 
                "Would you like to explore a related exercise?"],
                "choices": {
                    "yes": "ask_feigning_laughter",
                    "no": "continue_curr_not_willing"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            # self-laughter

            "ask_recent_error": {
                "model_prompt": "Have you made any errors or blunders recently? Nothing major, just in your day-to-day life.",
                "choices": {
                    "yes": "ask_laugher_error", 
                    "no": "no_error",
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "ask_laugher_error": {  
                "model_prompt": laughed_off,
                "choices": {
                    "yes": "ask_feel_post_error", 
                    "no": "encourage_laughter_error",
                },
                "protocols": {
                    "yes": [],
                    "no": [], 
                },
            },

            "ask_feel_post_error": {  
                "model_prompt": ask_post_protocol_feeling,
                "choices": {
                    "Better": "try_post_protocol_pos",
                    "Worse": lambda user_id, db_session, curr_session, app: self.check_contempt_post_error(user_id),
                    "No change": lambda user_id, db_session, curr_session, app: self.check_contempt_post_error(user_id),
                },
                "protocols": {
                    "Better": [],
                    "Worse": [],
                    "No change": [],
                },
            },

            "remind_contempt_post_error": { 
                "model_prompt": [empathetic_response_neg, not_contempt], 
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
                "model_prompt": further_clarification,
                "choices": {
                    "yes": "further_clarify_post_error", 
                    "no": "try_post_protocol_neg"
                }, 
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "further_clarify_post_error": { 
                # TODO
                "model_prompt": [clarify_errors_protocol_and_example_1, clarify_errors_protocol_and_example_2, look_at_sheet], 
                "choices": {
                    "continue": "try_post_protocol_neg",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "how_not_contempt_post_error":{
                "model_prompt": [how_not_contempt, further_clarification], 
                "choices": {
                    "yes": "further_clarify_post_error", 
                    "no": "try_post_protocol_neg" 
                }, 
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "post_error_neg": { 
                "model_prompt": [empathetic_response_neg, further_clarification],
                "choices": {
                    "yes": "further_clarify_post_error", 
                    "no": "try_post_protocol_neg"
                }, 
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "encourage_laughter_error": {
                "model_prompt": ["Feel free to practice laughing at this in your own time, along with any other minor errors in the future.",
                "And don\'t be embarrassed, I\'m sure mine are much worse!"],
                "choices": {
                    "continue": "ask_feel_pre_error",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "ask_feel_pre_error": {
                "model_prompt": ask_pre_protocol_feeling,
                "choices": {
                    "Positive": "continue_pos_pre_protocol",
                    "Negative": lambda user_id, db_session, curr_session, app: self.check_contempt_pre_error(user_id),
                    "Unsure": "explain_laughter_error"
                },
                "protocols": {
                    "Positive": [],
                    "Negative": [],
                    "Unsure": []
                },
            },

            "remind_contempt_pre_error": { 
                "model_prompt": [empathetic_response_neg, not_contempt], 
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
                "model_prompt": further_clarification, 
                "choices": {
                    "yes": "further_clarify_pre_error",
                    "no": "try_pre_protocol_neg"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "how_not_contempt_pre_error":{
                "model_prompt": [how_not_contempt, further_clarification], 
                "choices": {
                    "yes": "further_clarify_pre_error", 
                    "no": "try_pre_protocol_neg" 
                }, 
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "pre_error_neg": {
                "model_prompt": [empathetic_response_neg, further_clarification], 
                "choices": {
                    "yes": "further_clarify_pre_error",
                    "no": "try_pre_protocol_neg"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "further_clarify_pre_error": {
                "model_prompt": [clarify_errors_protocol_and_example_1, clarify_errors_protocol_and_example_2, look_at_sheet], 
                "choices": {
                    "continue": "try_pre_protocol_neg",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "explain_laughter_error": {
                "model_prompt": ["An example could be wearing two different colour socks to work by mistake.", 
                "A good ice breaker for everyone to laugh at when the conversation gets boring!"],  
                "choices": {
                    "continue": "continue_explaining_laughter_error",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "continue_explaining_laughter_error": {
                "model_prompt": ["You can try laughing at any of your errors on your own in the same way.", ask_pre_protocol_feeling],
                "choices": {
                    "Positive": "continue_pos_pre_protocol",
                    "Negative": lambda user_id, db_session, curr_session, app: self.check_contempt_pre_error(user_id)
                },
                "protocols": {
                    "Positive": [],
                    "Negative": []
                },
            },

            "no_error": {
                "model_prompt": ["Wow, I am jealous! I make mistakes all the time!", "Would you like to explore another more relevant context for laughter?"],
                "choices": {
                    #can't do it
                    "Yes": lambda user_id, db_session, curr_session, app: self.determine_next_tiny_session(user_id, "can't_do"), # TODO function that returns next prompt (random based on user's choice, emotion and current level)
                    "No, I'd like to continue exploring errors": "continue_exploring_error"
                },
                "protocols": {
                    "Yes": [],
                    "No, I'd like to continue exploring errors": []
                },
            },

            "continue_exploring_error": {
                "model_prompt": ["If you do recognise making any errors, try to become playful and laugh at them on your own.", 
                ask_pre_protocol_feeling],
                "choices": {
                    "Positive": "continue_pos_pre_protocol",
                    "Negative": lambda user_id, db_session, curr_session, app: self.check_contempt_pre_error(user_id)
                },
                "protocols": {
                    "Positive": [],
                    "Negative": []
                },
            },

            # setbacks

            "ask_setback": {
                "model_prompt": "Have you experienced any setbacks in your distant past?",
                "choices": {
                    "yes": "ask_laughter_setback",
                    "no": "empathetic_continue_curr_can't_do"
                },
                "protocols": {
                    "yes": [self.PROTOCOL_TITLES[11]],
                    "no": [self.PROTOCOL_TITLES[11]]
                },
            },

            "ask_laughter_setback": {
                "model_prompt": "Have you tried laughing at the setback, while changing your interpretation of this? Can you identify any positive aspects to this setback?",
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
                "model_prompt": ask_post_protocol_feeling,
                "choices": {
                    "Better": "try_post_protocol_pos",
                    "Worse": lambda user_id, db_session, curr_session, app: self.check_contempt_post_setback(user_id), #"post_setback_neg" #if already given contempt reminder otherwise, empathetic_response_neg, contempt, further_clar,
                    "No change": lambda user_id, db_session, curr_session, app: self.check_contempt_post_setback(user_id),
                },
                "protocols": {
                    "Better": [],
                    "Worse": [],
                    "No change": [],
                },
            },

            "remind_contempt_post_setback": {
                "model_prompt": [empathetic_response_neg, not_contempt], 
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
                "model_prompt": further_clarification,
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
                "model_prompt": [clarify_setbacks_protocol_and_example, look_at_sheet, try_this_again],
                "choices": {
                    "continue": "continue_curr_not_willing",
                },
                "protocols": {
                    "continue": [],
                },
            }, 

            "how_not_contempt_post_setback": {
                "model_prompt": [how_not_contempt, further_clarification], 
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
                "model_prompt": [empathetic_response_neg, further_clarification],
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
                "model_prompt": ask_want_to_try,
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
                "model_prompt": "Have you experienced this setback in the distant past and struggled with it for a long time?",
                "choices": {
                    "yes": "remind_objectives_setback",
                    "no": "propose_reflect_setback",
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "remind_objectives_setback": {
                "model_prompt": ["Nietzsche believes that failure and pain should be embraced and even desired.",
                "His quote captures this belief, and we should recite it while thinking about our setback.", 
                "The aim is to start laughing when completing the sentence: \"To those human beings who are of any concern to me I wish suffering...\", as this contradicts our deep-rooted beliefs, and then continue to laugh while reciting the rest of the quote.", 
                make_sense],
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
                "model_prompt": ["Here it is:",
                "", 
                "Let me know once you\'ve read this."],
                #TODO: check order!
                "choices": {
                    "Done": "encourage_laughter_setback", 
                },
                "protocols": {
                    "Done": [],
                },
            },

            "encourage_laughter_setback": {
                #TODO check encourage_setback_practice
                "model_prompt": [encourage_setback_practice, ask_pre_protocol_feeling],
                "choices": {
                    "Positive": "continue_pos_pre_protocol",
                    "Negative": lambda user_id, db_session, curr_session, app: self.check_contempt_pre_setback(user_id)#"pre_setback_neg"
                },
                "protocols": {
                    "Positive": [],
                    "Negative": [],
                },
            },

            "remind_contempt_pre_setback": {
                "model_prompt": not_contempt, 
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
                "model_prompt": review_protocols_and_return,
                "choices": {
                    "continue": "encourage_laughter_setback"
                },
                "protocols": {
                    "continue": [],
                },
            },           
            
            "pre_setback_neg": {
                "model_prompt": further_clarification,
                "choices": {
                    "yes": "further_clarify_pre_setback",
                    "no":  "try_pre_protocol_neg"# or "continue_curr_not_willing"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "further_clarify_pre_setback": {
                "model_prompt": [clarify_setbacks_protocol_and_example, look_at_sheet],
                "choices": {
                    "continue": "try_pre_protocol_neg"# or "continue_curr_not_willing",
                },
                "protocols": {
                    "continue": [],
                },
            }, 

            "how_not_contempt_pre_setback": {
                "model_prompt": [how_not_contempt, further_clarification], 
                "choices": {
                    "yes": "further_clarify_pre_setback", 
                    "no": "try_pre_protocol_neg" 
                }, 
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "propose_reflect_setback": {
                "model_prompt": ["It is important to take some time to reflect on any setbacks before attempting to laugh them off. We are not in a race!"],
                "choices": {
                    "continue": "continue_curr_can't_do",#lambda user_id, db_session, curr_session, app: self.check_contempt_pre_setback(user_id),
                },
                "protocols": {
                    "continue": [],
                },
            },

            "clarify_setback": {
                "model_prompt": ["This would involve you trying to change your interpretation of this setback and acknowledge any of its positive impacts.", 
                ask_want_to_try],
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
                "model_prompt": "Do you recognise any long-standing hardship or difficulty present in your life, such as an illness or loss?",
                "choices": {
                    "Yes": "ask_accept_hardship",
                    "No": "empathetic_continue_curr_can't_do", 
                    "Rather not say": "empathetic_response_hardship"
                },
                "protocols": {
                    "Yes": [self.PROTOCOL_TITLES[12]],
                    "No": [self.PROTOCOL_TITLES[12]],
                    "Rather not say": [self.PROTOCOL_TITLES[12]]
                },
            },

            "ask_accept_hardship": {
                "model_prompt": ["I\'ve found that it helps to come to terms with, accept and even try to \'love\' our hardships.", 
                "Have you tried this before?"],
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
                "model_prompt": ask_post_protocol_feeling,
                "choices": {
                    "Better": "try_post_protocol_pos",
                    "Worse": lambda user_id, db_session, curr_session, app: self.check_contempt_post_hardship(user_id),
                    "No change": lambda user_id, db_session, curr_session, app: self.check_contempt_post_hardship(user_id),
                },
                "protocols": {
                    "Better": [],
                    "Worse": [],
                    "No change": [],
                },
            },

            "remind_contempt_post_hardship": {
                "model_prompt": [empathetic_response_neg, not_contempt], 
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
                "model_prompt": [clarify_hardship_protocol, look_at_sheet],
                "choices": {
                    "continue": "try_post_protocol_neg",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "how_not_contempt_post_hardship": {
                "model_prompt": [how_not_contempt, further_clarification], 
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
                "model_prompt": [empathetic_response_neg, further_clarification],
                "choices": {
                    "yes": "further_clarify_post_hardship",
                    "no": lambda user_id, db_session, curr_session, app: self.check_contempt_post(user_id) 
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "ask_try_pre_hardship": {
                "model_prompt": ask_want_to_try, 
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
                "model_prompt": "Do you feel this hardship has been around for a long time and that you have had enough time to reflect on it?",
                "choices": {
                    "yes": "remind_objectives_hardship",
                    "no": "propose_reflect_hardship",
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "remind_objectives_hardship": {
                "model_prompt": ["In one of Nietzsche\'s quote, he encourages us not just to bear but to love everything that has happened to us, including our suffering, which contradicts our beliefs and therefore is funny.", 
                "The aim is to recite his quote while thinking about our hardship, laughing aloud when we reach the final words: \"but love it\".", 
                make_sense],
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
                "model_prompt": ["Here it is:",
                "", 
                "Let me know once you’ve read this."],
                #TODO: check order!
                "choices": {
                    "Done": "encourage_laughter_hardship", 
                },
                "protocols": {
                    "Done": [],
                },
            },

            "review_and_return_hardship": {
                "model_prompt": review_protocols_and_return,
                "choices": {
                    "continue": "encourage_laughter_hardship"
                },
                "protocols": {
                    "continue": [],
                },
            },

            "encourage_laughter_hardship": {
                "model_prompt": [encourage_hardship_practice, ask_pre_protocol_feeling],
                "choices": {
                    "Positive": "continue_pos_pre_protocol", 
                    "Negative": lambda user_id, db_session, curr_session, app: self.check_contempt_pre_hardship(user_id), 
                    "Unsure": "pre_hardship_neg"
                },
                "protocols": {
                    "Positive": [],
                    "Negative": [],
                    "Unsure": [],
                },
            },

            "remind_contempt_pre_hardship": {
                "model_prompt": not_contempt, 
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
                "model_prompt": further_clarification,
                "choices": {
                    "yes": "further_clarify_pre_hardship",
                    "no": "try_pre_protocol_neg" # or "continue_curr_not_willing",
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "how_not_contempt_pre_hardship": {
                "model_prompt": [how_not_contempt, further_clarification], 
                "choices": {
                    "yes": "further_clarify_pre_hardship", 
                    "no": "try_pre_protocol_neg" 
                }, 
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "further_clarify_pre_hardship": {
                #TODO check this
                "model_prompt": [clarify_hardship_protocol, look_at_sheet],
                "choices": {
                    "continue": "try_pre_protocol_neg",
                },
                "protocols": {
                    "continue": [],
                },
            }, 

            "propose_reflect_hardship": {
                "model_prompt": ["It is important to spend some time reflecting on any hardships before attempting to laugh them off.",
                "As they say, you can't run before you can walk!", #TODO
                ],
                "choices": {
                    "continue": "continue_curr_can't_do",#lambda user_id, db_session, curr_session, app: self.check_contempt_pre_setback(user_id),
                },
                "protocols": {
                    "continue": [],
                },
            },

            "clarify_hardship": {
                "model_prompt": ["This would involve developing a new interpretation of this hardship.",
                "Maybe it has made you wiser? Or has it brought about any benefits to your life?",
                "At the very least, simply surviving the hardship means that it has probably made you stronger.",
                ask_want_to_try],
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
                "model_prompt": ["No problem!", continue_other],
                "choices": {
                    #negative/rather not
                    "yes": lambda user_id, db_session, curr_session, app: self.determine_next_tiny_session(user_id, "not_willing"),
                    "no": "review_any_session"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            #################### MAIN SESSION (POSITIVE) ####################
            # pick from 3 mini sessions: 
            # 1) playful mode and self-glory: 
            # "ask_playful_mode" (see above)

            # 2) incongruity and contrasting views:
            "ask_incongruity_and_cv": {
                "model_prompt": "Have you experienced any incongruity in your life lately?",
                "choices": {
                    "Yes": "ask_laughter_incongruity",
                    "No": "no_incongruity_cv",
                    "Not sure": "reminder_incongruity",
                },
                "protocols": {
                    "Yes": [],
                    "No": [], 
                    "Not sure": []
                },
            },

            "no_incongruity_cv": {
                "model_prompt": ["I see. I hope you're not finding it too boring then!", 
                "How do you feel about the idea of exploiting a change in your perception of an image as a trigger for laughter?"],
                "choices": {
                    "Sounds interesting": "pre_cv_pos", 
                    "What?": "pre_cv_neg"
                },
                "protocols": {
                    "Sounds interesting": [self.PROTOCOL_TITLES[7]],
                    "What?": [self.PROTOCOL_TITLES[7]]
                },
            },
            
            # 3) own laughter brand and feigning laughter: 
            # "ask_laughter_brand" (see above)

            #################### MAIN SESSION (NEGATIVE)
            
            "underlying_reason_yes": {
                "model_prompt": ask_pre_protocol_feeling_laughter,
                "choices": {
                    "yes": "pre_laughter_pos",
                    "no": "pre_laughter_neg", 
                },
                "protocols": {
                    #"yes": [self.PROTOCOL_TITLES[9], self.PROTOCOL_TITLES[10], self.PROTOCOL_TITLES[11]], #change here?
                    #[self.PROTOCOL_TITLES[k] for k in self.positive_protocols],
                    "yes": [],
                    "no": [],
                },
            },

            "pre_laughter_pos": {
                "model_prompt": ["How do you feel you can laugh it off? Do any of these theories seem applicable?", 
                "If you're unsure, feel free to review them (on the right)."],
                "choices": {
                    "Superiority": "propose_laugh_off",
                    "Incongruity": "propose_laugh_off",
                    "Playful": "propose_laugh_off",
                    "A combination of these": "propose_laugh_off",
                    "Other": "propose_laugh_off",

                },
                "protocols": {
                    #"yes": [self.PROTOCOL_TITLES[9], self.PROTOCOL_TITLES[10], self.PROTOCOL_TITLES[11]], #change here?
                    #[self.PROTOCOL_TITLES[k] for k in self.positive_protocols],
                    "Superiority": [],
                    "Incongruity": [],
                    "Playful": [],
                    "A combination of these": [],
                    "Other": [],
                },
            },

            "propose_laugh_off": {
                "model_prompt": ["It\'s great that you can recognise the context behind laughing it off.", ask_pre_protocol_feeling],
                "choices": {
                    "\U0001F600": "try_pre_protocol_pos",
                    "\U0001F641": lambda user_id, db_session, curr_session, app: self.check_contempt(user_id)
                },
                "protocols": {
                    #"yes": [self.PROTOCOL_TITLES[9], self.PROTOCOL_TITLES[10], self.PROTOCOL_TITLES[11]], #change here?
                    #[self.PROTOCOL_TITLES[k] for k in self.positive_protocols],
                    "\U0001F600": [],
                    "\U0001F641": [],
                },
            },

            # TODO
            #"propose_laugh_off": {
            #    "model_prompt": ["It\'s great that you can recognise the context behind laughing it off.", ask_pre_protocol_feeling],
            #    "choices": {
            #        "\U0001F600": "try_pre_protocol_pos",
            #        "\U0001F610": lambda user_id, db_session, curr_session, app: self.check_contempt(user_id),
            #        "\U0001F641": lambda user_id, db_session, curr_session, app: self.check_contempt(user_id)
            #    },
            #    "protocols": {
            #        #"yes": [self.PROTOCOL_TITLES[9], self.PROTOCOL_TITLES[10], self.PROTOCOL_TITLES[11]], #change here?
            #        #[self.PROTOCOL_TITLES[k] for k in self.positive_protocols],
            #        "\U0001F600": [],
            #        "\U0001F610": [],
            #        "\U0001F641": [],
            #    },
            #},

            "remind_contempt_pre_laughter": {
                # TODO: what response?
                "model_prompt": [empathetic_response_neg, not_contempt], 
                "choices": {
                    "Sure": "try_pre_protocol_neg", 
                    "How can I stop this?": "try_pre_protocol_neg_no_contempt",
                },
                "protocols": {
                    "Sure": [],
                    "How can I stop this?": []
                },
            },
            
            "encourage_laughter": {
                "model_prompt": [empathetic_resp_neg_pre, try_this],
                "choices": {
                    "continue": "continue_curr_not_willing",
                },
                "protocols": {
                    "continue": [],
                },
            },

            "pre_laughter_neg": {
                # TODO: check
                "model_prompt": further_clarification,
                "choices": {
                    "yes": "clarify_laughter",
                    "no": lambda user_id, db_session, curr_session, app: self.check_contempt_pre(user_id) 
                },
                "protocols": {
                    "yes": [],
                    "no": [], 
                },
            },

            "clarify_laughter": {
                "model_prompt": established_humour_context_and_sheet,
                "choices": {
                    "continue": "underlying_reason_yes"
                },
                "protocols": {
                    #"yes": [self.PROTOCOL_TITLES[9], self.PROTOCOL_TITLES[10], self.PROTOCOL_TITLES[11]], #change here?
                    #[self.PROTOCOL_TITLES[k] for k in self.positive_protocols],
                    "continue": [],
                },
            },

            "underlying_reason_no": {
                "model_prompt": "Would you like to explore the possible trigger?",
                "choices": {
                    "yes": "explore_trigger_yes",
                    "no": "continue_curr_not_willing",
                },
                "protocols": {
                    #"yes": [self.PROTOCOL_TITLES[9], self.PROTOCOL_TITLES[10], self.PROTOCOL_TITLES[11]], #change here?
                    #[self.PROTOCOL_TITLES[k] for k in self.positive_protocols],
                    "yes": [],
                    "no": []
                },
            },

            "explore_trigger_yes": {
                "model_prompt": "Do you think it could be an incongruity or inconsistency that\'s causing your negative feeling?",
                "choices": {
                    "Yes": "ask_laughter_incongruity",
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
                "model_prompt": "Maybe it’s an everyday error or flaw that you’ve noticed, that’s causing this negative feeling?",
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
                "model_prompt": ["An example could be, your school has extended its closing time by 30 minutes."],
                "choices": {
                    "continue": "explore_trigger_yes_no_unsure", 
                },
                "protocols": {
                    "continue": []
                },
            },

            "explore_trigger_yes_no_unsure": {
                "model_prompt": "Do you think it could be an incongruity or inconsistency that\'s causing your negative feeling?",
                "choices": {
                    "yes": "ask_laughter_incongruity", # trigger is incongruity -> SKIP TO TINY-SESSION
                    "no": "trigger_not_incongruity",
                },
                "protocols": {
                    "yes": [],
                    "no": [],
                },
            },

            "trigger_not_error": {
                "model_prompt": "Would you like to explore more involved possible triggers for your negative feeling?",
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
                "model_prompt": "Could it be a distant setback that\'s causing this negative feeling?",
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
                "model_prompt": "Are you facing a long-term hardship that\'s causing this negative feeling?",
                "choices": {
                    "yes": "ask_accept_hardship", 
                    "no": "trigger_not_hardship",
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            "trigger_not_hardship": {
                "model_prompt": ["It seems that the underlying reason is hiding from us at the moment.", 
                "Not to worry, feeling down is not unusual, and hopefully, this feeling should pass. However, if you suspect it's not improving or things don't feel quite right, it's worth checking up with your doctor.", 
                "But for now, would you like to explore other contexts for humour?"], 
                "choices": {
                    "yes": lambda user_id, db_session, curr_session, app: self.determine_next_tiny_session(user_id, "can't_do"), 
                    "no": "review_any_session"
                },
                "protocols": {
                    "yes": [],
                    "no": []
                },
            },

            #################### END MAIN SESSION (NEGATIVE)

            "event_is_recent": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_event_is_recent(user_id, app, db_session),

                "choices": {
                    "It was recent": "revisiting_recent_events",
                    "It was distant": "revisiting_distant_events",
                },
                "protocols": {
                    "It was recent": [],
                    "It was distant": []
                    },
            },

            "revisiting_recent_events": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_revisit_recent(user_id, app, db_session),

                "choices": {
                    "yes": "more_questions",
                    "no": "more_questions",
                },
                "protocols": {
                    "yes": [self.PROTOCOL_TITLES[7], self.PROTOCOL_TITLES[8]],
                    "no": [self.PROTOCOL_TITLES[11]],
                },
            },

            "revisiting_distant_events": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_revisit_distant(user_id, app, db_session),

                "choices": {
                    "yes": "more_questions",
                    "no": "more_questions",
                },
                "protocols": {
                    "yes": [self.PROTOCOL_TITLES[3], self.PROTOCOL_TITLES[7]],
                    "no": [self.PROTOCOL_TITLES[6]]
                },
            },

            "more_questions": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_more_questions(user_id, app, db_session),

                "choices": {
                    "Okay": lambda user_id, db_session, curr_session, app: self.get_next_question(user_id),
                    "I'd rather not": "project_emotion",
                },
                "protocols": {
                    "Okay": [],
                    "I'd rather not": [self.PROTOCOL_TITLES[3]],
                },
            },

            "displaying_antisocial_behaviour": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_antisocial(user_id, app, db_session),

                "choices": {
                    "yes": "project_emotion",
                    "no": lambda user_id, db_session, curr_session, app: self.get_next_question(user_id),
                },
                "protocols": {
                    "yes": [self.PROTOCOL_TITLES[3], self.PROTOCOL_TITLES[4]],
                    "no": [self.PROTOCOL_TITLES[3]],
                },
            },

            "internal_persecutor_saviour": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_saviour(user_id, app, db_session),

                "choices": {
                    "yes": "project_emotion",
                    "no": "internal_persecutor_victim",
                },
                "protocols": {
                    "yes": [], #self.INTERNAL_PERSECUTOR_PROTOCOLS,
                    "no": []
                },
            },

            "internal_persecutor_victim": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_victim(user_id, app, db_session),

                "choices": {
                    "yes": "project_emotion",
                    "no": "internal_persecutor_controlling",
                },
                "protocols": {
                    "yes": [], #self.INTERNAL_PERSECUTOR_PROTOCOLS,
                    "no": []
                },
            },

            "internal_persecutor_controlling": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_controlling(user_id, app, db_session),

                "choices": {
                "yes": "project_emotion",
                "no": "internal_persecutor_accusing"
                },
                "protocols": {
                "yes": [],#self.INTERNAL_PERSECUTOR_PROTOCOLS,
                "no": []
                },
            },

            "internal_persecutor_accusing": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_accusing(user_id, app, db_session),

                "choices": {
                "yes": "project_emotion",
                "no": lambda user_id, db_session, curr_session, app: self.get_next_question(user_id),
                },
                "protocols": {
                "yes": [],#self.INTERNAL_PERSECUTOR_PROTOCOLS,
                "no": [self.PROTOCOL_TITLES[3]],
                },
            },

            "rigid_thought": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_rigid_thought(user_id, app, db_session),

                "choices": {
                    "yes": lambda user_id, db_session, curr_session, app: self.get_next_question(user_id),
                    "no": "project_emotion",
                },
                "protocols": {
                    "yes": [self.PROTOCOL_TITLES[3]],
                    "no": [self.PROTOCOL_TITLES[3], self.PROTOCOL_TITLES[9]],
                },
            },

            "personal_crisis": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_personal_crisis(user_id, app, db_session),

                "choices": {
                    "yes": "project_emotion",
                    "no": lambda user_id, db_session, curr_session, app: self.get_next_question(user_id),
                },
                "protocols": {
                    "yes": [self.PROTOCOL_TITLES[3], self.PROTOCOL_TITLES[7]],
                    "no": [self.PROTOCOL_TITLES[3]],
                },
            },

            #################### ALL EMOTIONS ####################

            "project_emotion": {
               "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_project_emotion(user_id, app, db_session),

               "choices": {
                   "Continue": "suggestions",
               },
               "protocols": {
                   "Continue": [],
               },
            },

            "suggestions": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_suggestions(user_id, app, db_session),

                "choices": {
                     self.PROTOCOL_TITLES[k]: "trying_protocol" #self.current_protocol_ids[user_id]
                     for k in self.positive_protocols
                },
                "protocols": {
                     self.PROTOCOL_TITLES[k]: [self.PROTOCOL_TITLES[k]]
                     for k in self.positive_protocols
                },
            },

            "trying_protocol": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_trying_protocol(user_id, app, db_session),

                "choices": {"continue": "user_found_useful"},
                "protocols": {"continue": []},
            },

            "user_found_useful": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_found_useful(user_id, app, db_session),

                "choices": {
                    "Better": "new_protocol_better",
                    "Worse": "new_protocol_worse",
                    "No change": "new_protocol_same",
                },
                "protocols": {
                    "Better": [],
                    "Worse": [],
                    "No change": [],
                },
            },

            "new_protocol_better": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_new_better(user_id, app, db_session),

                "choices": {
                    "Yes (show follow-up suggestions)": lambda user_id, db_session, curr_session, app: self.determine_next_prompt_new_protocol(
                        user_id, app
                    ),
                    "Yes (restart questions)": "restart_prompt",
                    "No (end session)": "ending_prompt",
                },
                "protocols": {
                    "Yes (show follow-up suggestions)": [],
                    "Yes (restart questions)": [],
                    "No (end session)": []
                },
            },

            "new_protocol_worse": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_new_worse(user_id, app, db_session),

                "choices": {
                    "Yes (show follow-up suggestions)": lambda user_id, db_session, curr_session, app: self.determine_next_prompt_new_protocol(
                        user_id, app
                    ),
                    "Yes (restart questions)": "restart_prompt",
                    "No (end session)": "ending_prompt",
                },
                "protocols": {
                    "Yes (show follow-up suggestions)": [],
                    "Yes (restart questions)": [],
                    "No (end session)": []
                },
            },

            "new_protocol_same": {
                "model_prompt": [
                                "I am sorry to hear you have not detected any change in your mood.",
                                "That can sometimes happen but if you agree we could try another protocol and see if that is more helpful to you.",
                                "Would you like me to suggest a different protocol?"
                                ],

                "choices": {
                    "Yes (show follow-up suggestions)": lambda user_id, db_session, curr_session, app: self.determine_next_prompt_new_protocol(
                        user_id, app
                    ),
                    "Yes (restart questions)": "restart_prompt",
                    "No (end session)": "ending_prompt",
                },
                "protocols": {
                    "Yes (show follow-up suggestions)": [],
                    "Yes (restart questions)": [],
                    "No (end session)": []
                },
            },

            "ending_prompt": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_model_prompt_ending(user_id, app, db_session),

                "choices": {"any": "opening_prompt"},
                "protocols": {"any": []}
            },

            "restart_prompt": {
                "model_prompt": lambda user_id, db_session, curr_session, app: self.get_restart_prompt(user_id),

                "choices": {
                    "open_text": lambda user_id, db_session, curr_session, app: self.determine_next_prompt_opening(user_id, app, db_session)
                },
                "protocols": {"open_text": []},
            },
        }
        self.QUESTION_KEYS = list(self.QUESTIONS.keys())

    def initialise_prev_questions(self, user_id):
        self.recent_questions[user_id] = []

    def clear_persona(self, user_id):
        self.chosen_personas[user_id] = ""

    def clear_names(self, user_id):
        self.users_names[user_id] = ""

    def clear_datasets(self, user_id):
        self.datasets[user_id] = pd.DataFrame(columns=['sentences'])

    def initialise_remaining_choices(self, user_id):
        self.remaining_choices[user_id] = ["displaying_antisocial_behaviour", "internal_persecutor_saviour", "personal_crisis", "rigid_thought"]

    def initialise_user_tiny_sessions(self, user_id):
        # TODO: FOR NOW!!!!!!!
        # drop negative once donne (from list!)
        self.user_tiny_sessions[user_id] = ("1: Playful mind", "2: Playful face")
    
    def initialise_user_covered_sessions(self, user_id):
        self.user_covered_sessions[user_id] = []

    def initialise_contempt_message(self, user_id):
        self.contempt_message[user_id] = False

    def save_name(self, user_id):
        try:
            user_response = self.user_choices[user_id]["choices_made"]["ask_name"]
        except:  # noqa
            user_response = ""
        self.users_names[user_id] = user_response
        self.chosen_personas[user_id] = "Kai"
        self.datasets[user_id] = self.kai
        return "opening_prompt"
    
    def check_acknowledge_achievements(self, user_id):
        if ('3: Self-glory',) in self.user_covered_sessions[user_id]: 
            return "continue_curr_can't_do" 
        return "ask_self_glory"

    def check_contempt(self, user_id):
        if self.contempt_message[user_id] == False: 
            self.contempt_message[user_id] = True
            return "remind_contempt_pre_laughter" 
        return "encourage_laughter"

    def check_contempt_pre(self, user_id):
        if self.contempt_message[user_id] == False: 
            self.contempt_message[user_id] = True
            return "remind_contempt_pre_protocol" 
        else: return "continue_curr_not_willing"
    
    def check_contempt_post(self, user_id):
        if self.contempt_message[user_id] == False: 
            self.contempt_message[user_id] = True
            return "remind_contempt_post_protocol"
        else: return "try_post_protocol_neg"
    
    def check_contempt_post_error(self, user_id):
        print("contempt_message shown?: ", self.contempt_message[user_id])
        if self.contempt_message[user_id] == False: 
            self.contempt_message[user_id] = True
            return "remind_contempt_post_error"
        else: return "post_error_neg"

    def check_contempt_post_setback(self, user_id):
        if self.contempt_message[user_id] == False: 
            self.contempt_message[user_id] = True
            return "remind_contempt_post_setback"
        else: return "post_setback_neg"

    def check_contempt_post_hardship(self, user_id):
        if self.contempt_message[user_id] == False: 
            self.contempt_message[user_id] = True
            return "remind_contempt_post_hardship"
        else: return "post_hardship_neg"
    
    def check_contempt_pre_error(self, user_id):
        if self.contempt_message[user_id] == False: 
            self.contempt_message[user_id] = True
            return "remind_contempt_pre_error"
        else: return "pre_error_neg"
    
    def check_contempt_pre_setback(self, user_id):
        if self.contempt_message[user_id] == False: 
            self.contempt_message[user_id] = True
            return "remind_contempt_pre_setback"
        else: return "pre_setback_neg"

    def check_contempt_pre_hardship(self, user_id):
        if self.contempt_message[user_id] == False: 
            self.contempt_message[user_id] = True
            return "remind_contempt_pre_hardship"
        else: return "pre_hardship_neg"
        
    # TODO: add a time delay?
    def end_session(self, user_id):
        if self.user_states_initial[user_id] == "Negative":
            return "final_feeling_check"
        else:
            return "ending_session_initial_pos"
           
    def want_another_session(self, user_id):
        if self.users_names[user_id] == "":
            message = ["Glad to hear it."]
        else:
            message = ["Glad to hear it " + self.users_names[user_id] + "."]
        message.append("Feel free to reload the page and re-enter your credentials and we can have another chat!")
        return message
    
    def get_ending_message(self, user_id):
        if self.users_names[user_id] == "":
            message = ["Thanks! I hope you enjoyed our conversation and that we speak again soon."]
        else:
            message = ["Thanks " + self.users_names[user_id] + "! I hope you enjoyed our conversation and that we speak again soon."]
        return message

    def get_suggestions(self, user_id, app): #from all the lists of protocols collected at each step of the dialogue it puts together some and returns these as suggestions
        suggestions = []
        for curr_suggestions in list(self.suggestions[user_id]):
            if len(curr_suggestions) > 2:
                i, j = random.choices(range(0,len(curr_suggestions)), k=2)
                if curr_suggestions[i] and curr_suggestions[j] in self.PROTOCOL_TITLES: #weeds out some gibberish that im not sure why it's there
                    suggestions.extend([curr_suggestions[i], curr_suggestions[j]])
            else:
                suggestions.extend(curr_suggestions)
            suggestions = set(suggestions)
            suggestions = list(suggestions)
        while len(suggestions) < 4: #augment the suggestions if less than 4, we add random ones avoiding repetitions
            p = random.choice([i for i in range(1,12) if i not in [6,11]]) #we dont want to suggest protocol 6 or 11 at random here
            if (any(self.PROTOCOL_TITLES[p] not in curr_suggestions for curr_suggestions in list(self.suggestions[user_id]))
                and self.PROTOCOL_TITLES[p] not in self.recent_protocols and self.PROTOCOL_TITLES[p] not in suggestions):
                        suggestions.append(self.PROTOCOL_TITLES[p])
                        self.suggestions[user_id].extend([self.PROTOCOL_TITLES[p]])
        return suggestions

    def clear_suggestions(self, user_id):
        self.suggestions[user_id] = []
        self.reordered_protocol_questions[user_id] = deque(maxlen=5)

    def clear_emotion_scores(self, user_id):
        self.guess_emotion_predictions[user_id] = ""

    def create_new_run(self, user_id, db_session, user_session):
        new_run = UserModelRun(session_id=user_session.id)
        db_session.add(new_run)
        db_session.commit()
        self.current_run_ids[user_id] = new_run.id
        return new_run

    def clear_choices(self, user_id):
        self.user_choices[user_id] = {}

    # TODO change this and remove print statements
    def update_suggestions(self, user_id, protocols, app):

        # Check if user_id already has suggestions
        try:
            self.suggestions[user_id]
        except KeyError:
            self.suggestions[user_id] = []

        if type(protocols) != list:
            self.suggestions[user_id].append(deque([protocols]))
        else:
            self.suggestions[user_id].append(deque(protocols))

        print("self.suggestions[user_id]: ", self.suggestions[user_id])

    # Takes next item in queue, or moves on to suggestions
    # if all have been checked

    # add check for whether user is familiar with the humorous protocols
    def get_opening_prompt(self, user_id):
        # time.sleep(7)
        if self.users_names[user_id] == "":
            opening_prompt = ["Nice to speak to you. I will do my best to help you learn to laugh.", # \N{grinning face with smiling eyes}
            "Are you familiar with the self-initiated humorous protocols?"]
        else:
            opening_prompt = ["Nice to speak to you " + self.users_names[user_id] + ". I will do my best to help you learn to laugh.", # \N{grinning face with smiling eyes}
            "Are you familiar with the self-initiated humorous protocols?"]
        return opening_prompt

    def get_restart_prompt(self, user_id):
        #TODO: why time.sleep()
        time.sleep(7)
        if self.users_names[user_id] == "":
            restart_prompt = ["Please tell me again, how are you feeling today?"]
        else:
            restart_prompt = ["Please tell me again, " + self.users_names[user_id] + ", how are you feeling today?"]
        return restart_prompt
    
    # TODO added (right place)
    #def choose_tiny_session(self, user_id): 
    #from user_id: current emotional state, current protocol/level, previous protocols 
    # state can be "Positive" (Better), "Negative" (Worse) or "Neutral" (Same) 
    def determine_next_tiny_session(self, user_id, state):
        sessions_left = list(set(self.TINY_SESSION_TITLES) - set(self.user_covered_sessions[user_id]))
        print("self.user_covered_sessions: ", self.user_covered_sessions)
        print("sessions_left: ", sessions_left)
        next_session_options = set() #random non recent if no options or if user's finnished all - suggest they chooose

        current_state = self.user_states[user_id]
        current_session = self.user_tiny_sessions[user_id]
        print("current_session: ", current_session)
        current_level = self.TINY_SESSION_TITLE_TO_LEVEL[current_session]

        if len(sessions_left) > 0:
            sorted_sessions = sorted(sessions_left,key=self.TINY_SESSION_TITLES.index)
            min_session_level = self.TINY_SESSION_TITLE_TO_LEVEL[sorted_sessions[0]]

            print("sorted sessions: ", sorted_sessions)
            print("min_session_level: ", min_session_level)
            for session in sessions_left:
                session_level = self.TINY_SESSION_TITLE_TO_LEVEL[session]
                print("session_level: ", session_level)
                if current_state == "Positive":
                    if state == "willing":
                        if session_level >= current_level:
                            next_session_options.add(session)
                    elif state == "not_willing":
                        if session_level <= current_level:
                            next_session_options.add(session)
                    elif state == "can't_do":
                        if current_level < 3 and session_level == current_level + 1:
                            next_session_options.add(session)
                elif current_state == "Negative":
                    # User can’t do current protocol due to circumstance: Random protocol from session pool with level <= current protocol level
                    # User doesn’t want to do a protocol: Random protocol from session pool with lowest level protocol
                    # User would like to continue: Random protocol from session pool with level <= current protocol level
                    if state == "Positive":
                        print("I'm negative and positive!!!!!")
                        if session_level <= current_level:
                            next_session_options.add(session)
                    elif state == "Negative":
                        print("I'm negative and negative!!!!!")
                        if session_level == min_session_level:
                            next_session_options.add(session)
                    elif state == "Neutral":
                        print("I'm negative and neutral!!!!!")
                        if session_level <= current_level:
                            next_session_options.add(session)
        else:
            # covered all tiny sessions
            return "covered_all_sessions"
        if next_session_options == set():
            print("THERE ARE NO next_session_options")
            random_choice = random.sample(sessions_left, 1)
            next_session_options.add(tuple(random_choice)[0])
            #next_session_options.add(np.random.choice(sessions_left))

        random_choice = random.sample(next_session_options, 1)
        return self.TINY_SESSION_TO_QUESTION[tuple(random_choice)[0]]
        return self.TINY_SESSION_TO_QUESTION[np.random.choice(next_session_options)]

    # TODO 
    def get_next_question(self, user_id):
        if self.remaining_choices[user_id] == []:
            return "project_emotion"
        else:
            selected_choice = np.random.choice(self.remaining_choices[user_id])
            self.remaining_choices[user_id].remove(selected_choice)
            return selected_choice

    def add_to_reordered_protocols(self, user_id, next_protocol):
        self.reordered_protocol_questions[user_id].append(next_protocol)

    def add_to_next_protocols(self, next_protocols):
        self.protocols_to_suggest.append(deque(next_protocols))

    def clear_suggested_protocols(self):
        self.protocols_to_suggest = []

    # NOTE: this is not currently used, but can be integrated to support
    # positive protocol suggestions (to avoid recent protocols).
    # You would need to add it in when a user's emotion is positive
    # and they have chosen a protocol.

    def add_to_recent_protocols(self, recent_protocol):
        if len(self.recent_protocols) == self.recent_protocols.maxlen:
            # Removes oldest protocol
            self.recent_protocols.popleft()
        self.recent_protocols.append(recent_protocol)

    # previously determine_next_prompt_opening - get emotion at start of session
    def determine_next_prompt_start_session(self, user_id, app, db_session):
        user_response = self.user_choices[user_id]["choices_made"]["ask_emotion"]
        emotion = user_response.lower()
        if emotion == 'sad' or emotion == 'angry' or emotion == 'anxious' or emotion == 'happy':
            self.user_emotions[user_id] = string.capwords(user_response)
            if user_response.lower() == 'happy':
                #self.get_happy_emotion(user_id)
                self.user_states[user_id] = "Positive"
                self.user_states_initial[user_id] = "Positive"
                return "after_classification_positive"
            else:
                self.user_states[user_id] = "Negative"
                self.user_states_initial[user_id] = "Negative"
                return "after_classification_negative"
        
        emotion = get_emotion(user_response)
        #emotion = np.random.choice(["Happy", "Sad", "Angry", "Anxious"]) #random choice to be replaced with emotion classifier
        if emotion == 'fear':
            self.guess_emotion_predictions[user_id] = 'Anxious/Scared'
            self.user_emotions[user_id] = 'Anxious'
            self.user_states_initial[user_id] = 'Negative'
        elif emotion == 'sadness':
            self.guess_emotion_predictions[user_id] = 'Sad'
            self.user_emotions[user_id] = 'Sad'
            self.user_states_initial[user_id] = 'Negative'
        elif emotion == 'anger':
            self.guess_emotion_predictions[user_id] = 'Angry'
            self.user_emotions[user_id] = 'Angry'
            self.user_states_initial[user_id] = 'Negative'
        else:
            self.guess_emotion_predictions[user_id] = 'Happy/Content'
            self.user_emotions[user_id] = 'Happy'
            self.user_states_initial[user_id] = 'Positive'
        #self.guess_emotion_predictions[user_id] = emotion
        #self.user_emotions[user_id] = emotion
        self.user_states[user_id] = self.user_states_initial[user_id]
        return "guess_emotion"

    def get_best_sentence(self, column, prev_qs):
        #return random.choice(column.dropna().sample(n=15).to_list()) #using random choice instead of machine learning
        maxscore = 0
        chosen = ''
        for row in column.dropna().sample(n=5): #was 25
             fitscore = get_sentence_score(row, prev_qs)
             if fitscore > maxscore:
                 maxscore = fitscore
                 chosen = row
        if chosen != '':
            return chosen
        else:
            return random.choice(column.dropna().sample(n=5).to_list()) #was 25


    def split_sentence(self, sentence):
        temp_list = re.split('(?<=[.?!]) +', sentence)
        if '' in temp_list:
            temp_list.remove('')
        temp_list = [i + " " if i[-1] in [".", "?", "!"] else i for i in temp_list]
        if len(temp_list) == 2:
            return temp_list[0], temp_list[1]
        elif len(temp_list) == 3:
            return temp_list[0], temp_list[1], temp_list[2]
        else:
            return sentence

    # TODO: use this as a template for the rest
    def get_model_prompt_guess_emotion(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        column = data["All emotions - From what you have said I believe you are feeling {}. Is this correct?"].dropna()
        my_string = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(my_string)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(my_string)
        question = my_string.format(self.guess_emotion_predictions[user_id].lower())
        return self.split_sentence(question)

    # TODO: keep this
    def get_model_prompt_check_emotion(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        column = data["All emotions - I am sorry. Please select from the emotions below the one that best reflects what you are feeling:"].dropna()
        my_string = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(my_string)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(my_string)
        return self.split_sentence(my_string)

    def get_sad_emotion(self, user_id):
        self.guess_emotion_predictions[user_id] = "Sad"
        self.user_emotions[user_id] = "Sad"
        self.user_states_initial[user_id] = "Negative"
        self.user_states[user_id] = "Negative"
        return "after_classification_negative"

    def get_angry_emotion(self, user_id):
        self.guess_emotion_predictions[user_id] = "Angry"
        self.user_emotions[user_id] = "Angry"
        self.user_states_initial[user_id] = "Negative"
        self.user_states[user_id] = "Negative"
        return "after_classification_negative"

    def get_anxious_emotion(self, user_id):
        self.guess_emotion_predictions[user_id] = "Anxious/Scared"
        self.user_emotions[user_id] = "Anxious"
        self.user_states_initial[user_id] = "Negative"
        self.user_states[user_id] = "Negative"
        return "after_classification_negative" 

    def get_happy_emotion(self, user_id):
        self.guess_emotion_predictions[user_id] = "Happy/Content"
        self.user_emotions[user_id] = "Happy"
        self.user_states_initial[user_id] = "Positive"
        self.user_states[user_id] = "Positive"
        return "after_classification_positive"

    # TODO added (check right place)
    def determine_first_mini_session(self):
        mini_sessions = ["ask_playful_mode", "ask_incongruity_and_cv", "ask_laughter_brand"]
        chosen_session = np.random.choice(mini_sessions)
        return chosen_session
    
    def get_opening_prompt_negative(self, user_id):
        # time.sleep(7) TODO: decide how long
        state = self.user_emotions[user_id]
        emotion = self.get_emotional_state(state)
        if emotion == "":
            opening_prompt = ["Sorry to hear that. Can you identify the underlying reason behind this feeling?", 
            "You don\'t need to share the reason."]
        else:
            opening_prompt = ["Sorry to hear that. Can you identify the underlying reason behind your " + emotion + "?", 
            "You don\'t need to share the reason."]
        return opening_prompt
    
    def get_emotional_state(self, user_emotion):
        emotion = ""
        if user_emotion == "Angry":
            emotion = "anger"
        elif user_emotion == "Anxious":
            emotion = "fear"
        elif user_emotion == "Sad":
            emotion = "sadness"
        return emotion

    # TODO: add my get_model_prompt_s
    # use a couple of original: add 1 or 2 items to the dataset - ending, opening, guessing emotion, etc.




    def get_model_prompt_project_emotion(self, user_id, app, db_session):
        #time.sleep(7) # TODO: should we removed the sleeps
        if self.chosen_personas[user_id] == "Robert":
            prompt = "Ok, thank you. Now, one last important thing: since you've told me you're feeling " + self.user_emotions[user_id].lower() + ", I would like you to try to project this emotion onto your childhood self. You can press 'continue' when you are ready and I'll suggest some protocols I think may be appropriate for you."
        elif self.chosen_personas[user_id] == "Gabrielle":
            prompt = "Thank you, I will recommend some protocols for you in a moment. Before I do that, could you please try to project your " + self.user_emotions[user_id].lower() + " feeling onto your childhood self? Take your time to try this, and press 'continue' when you feel ready."
        elif self.chosen_personas[user_id] == "Arman":
            prompt = "Ok, thank you for letting me know that. Before I give you some protocol suggestions, please take some time to project your current " + self.user_emotions[user_id].lower() + " feeling onto your childhood self. Press 'continue' when you feel able to do it."
        elif self.chosen_personas[user_id] == "Arman":
            prompt = "Ok, thank you, I'm going to draw up a list of protocols which I think would be suitable for you today. In the meantime, going back to this " + self.user_emotions[user_id].lower() + " feeling of yours, would you like to try to project it onto your childhood self? You can try now and press 'continue' when you feel ready."
        else:
            prompt = "Thank you. While I have a think about which protocols would be best for you, please take your time now and try to project your current " + self.user_emotions[user_id].lower() + " emotion onto your childhood self. When you are able to do this, please press 'continue' to receive your suggestions."
        return self.split_sentence(prompt)


    def get_model_prompt_saviour(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        base_prompt = self.user_emotions[user_id] + " - Do you believe that you should be the saviour of someone else?"
        column = data[base_prompt].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_victim(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        base_prompt = self.user_emotions[user_id] + " - Do you see yourself as the victim, blaming someone else for how negative you feel?"
        column = data[base_prompt].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_controlling(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        base_prompt = self.user_emotions[user_id] + " - Do you feel that you are trying to control someone?"
        column = data[base_prompt].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_accusing(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        base_prompt = self.user_emotions[user_id] + " - Are you always blaming and accusing yourself for when something goes wrong?"
        column = data[base_prompt].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_specific_event(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        base_prompt = self.user_emotions[user_id] + " - Was this caused by a specific event/s?"
        column = data[base_prompt].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_event_is_recent(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        base_prompt = self.user_emotions[user_id] + " - Was this caused by a recent or distant event (or events)?"
        column = data[base_prompt].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_revisit_recent(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        base_prompt = self.user_emotions[user_id] + " - Have you recently attempted protocol 11 and found this reignited unmanageable emotions as a result of old events?"
        column = data[base_prompt].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_revisit_distant(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        base_prompt = self.user_emotions[user_id] + " - Have you recently attempted protocol 6 and found this reignited unmanageable emotions as a result of old events?"
        column = data[base_prompt].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_more_questions(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        base_prompt = self.user_emotions[user_id] + " - Thank you. Now I will ask some questions to understand your situation."
        column = data[base_prompt].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_antisocial(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        base_prompt = self.user_emotions[user_id] + " - Have you strongly felt or expressed any of the following emotions towards someone:"
        column = data[base_prompt].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return [self.split_sentence(question), "Envy, jealousy, greed, hatred, mistrust, malevolence, or revengefulness?"]

    def get_model_prompt_rigid_thought(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        base_prompt = self.user_emotions[user_id] + " - In previous conversations, have you considered other viewpoints presented?"
        column = data[base_prompt].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_personal_crisis(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        base_prompt = self.user_emotions[user_id] + " - Are you undergoing a personal crisis (experiencing difficulties with loved ones e.g. falling out with friends)?"
        column = data[base_prompt].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_happy(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        column = data["Happy - That's Good! Let me recommend a protocol you can attempt."].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_suggestions(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        column = data["All emotions - Here are my recommendations, please select the protocol that you would like to attempt"].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_trying_protocol(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        column = data["All emotions - Please try to go through this protocol now. When you finish, press 'continue'"].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return ["You have selected Protocol " + str(self.current_protocol_ids[user_id][0]) + ". ", self.split_sentence(question)]

    def get_model_prompt_found_useful(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        column = data["All emotions - Do you feel better or worse after having taken this protocol?"].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_new_better(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        column = data["All emotions - Would you like to attempt another protocol? (Patient feels better)"].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_new_worse(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        column = data["All emotions - Would you like to attempt another protocol? (Patient feels worse)"].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return self.split_sentence(question)

    def get_model_prompt_ending(self, user_id, app, db_session):
        prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
        data = self.datasets[user_id]
        column = data["All emotions - Thank you for taking part. See you soon"].dropna()
        question = self.get_best_sentence(column, prev_qs)
        if len(self.recent_questions[user_id]) < 50:
            self.recent_questions[user_id].append(question)
        else:
            self.recent_questions[user_id] = []
            self.recent_questions[user_id].append(question)
        return [self.split_sentence(question), "You have been disconnected. Refresh the page if you would like to start over."]


    def determine_next_prompt_new_protocol(self, user_id, app):
        try:
            self.suggestions[user_id]
        except KeyError:
            self.suggestions[user_id] = []
        if len(self.suggestions[user_id]) > 0:
            return "suggestions"
        return "more_questions"


    def determine_positive_protocols(self, user_id, app):
        protocol_counts = {}
        total_count = 0

        for protocol in self.positive_protocols:
            count = Protocol.query.filter_by(protocol_chosen=protocol).count()
            protocol_counts[protocol] = count
            total_count += count

        # for protocol in counts:
        if total_count > 10:
            first_item = min(zip(protocol_counts.values(), protocol_counts.keys()))[1]
            del protocol_counts[first_item]

            second_item = min(zip(protocol_counts.values(), protocol_counts.keys()))[1]
            del protocol_counts[second_item]

            third_item = min(zip(protocol_counts.values(), protocol_counts.keys()))[1]
            del protocol_counts[third_item]
        else:
            # CASE: < 10 protocols undertaken in total, so randomness introduced
            # to avoid lowest 3 being recommended repeatedly.
            # Gives number of next protocol to be suggested
            first_item = np.random.choice(
                list(set(self.positive_protocols) - set(self.recent_protocols))
            )
            second_item = np.random.choice(
                list(
                    set(self.positive_protocols)
                    - set(self.recent_protocols)
                    - set([first_item])
                )
            )
            third_item = np.random.choice(
                list(
                    set(self.positive_protocols)
                    - set(self.recent_protocols)
                    - set([first_item, second_item])
                )
            )

        return [
            self.PROTOCOL_TITLES[first_item],
            self.PROTOCOL_TITLES[second_item],
            self.PROTOCOL_TITLES[third_item],
        ]

    def determine_protocols_keyword_classifiers(
        self, user_id, db_session, curr_session, app
    ):

        # We add "suggestions" first, and in the event there are any left over we use those, otherwise we divert past it.
        self.add_to_reordered_protocols(user_id, "suggestions")

        # Default case: user should review protocols 13 and 14.
        #self.add_to_next_protocols([self.PROTOCOL_TITLES[13], self.PROTOCOL_TITLES[14]])
        return self.get_next_protocol_question(user_id, app)


    def update_conversation(self, user_id, new_dialogue, db_session, app):
        try:
            session_id = self.user_choices[user_id]["current_session_id"]
            curr_session = UserModelSession.query.filter_by(id=session_id).first()
            if curr_session.conversation is None:
                curr_session.conversation = "" + new_dialogue
            else:
                curr_session.conversation = curr_session.conversation + new_dialogue
            curr_session.last_updated = datetime.datetime.utcnow()
            db_session.commit()
        except KeyError:
            curr_session = UserModelSession(
                user_id=user_id,
                conversation=new_dialogue,
                last_updated=datetime.datetime.utcnow(),
            )

            db_session.add(curr_session)
            db_session.commit()
            self.user_choices[user_id]["current_session_id"] = curr_session.id


    def save_current_choice(
        self, user_id, input_type, user_choice, user_session, db_session, app
    ):
        # Set up dictionary if not set up already
        # with Session() as session:

        try:
            self.user_choices[user_id]
        except KeyError:
            self.user_choices[user_id] = {}

        # Define default choice if not already set
        try:
            current_choice = self.user_choices[user_id]["choices_made"][
                "current_choice"
            ]
        except KeyError:
            current_choice = self.QUESTION_KEYS[0]

        try:
            self.user_choices[user_id]["choices_made"]
        except KeyError:
            self.user_choices[user_id]["choices_made"] = {}

        if current_choice == "ask_name":
            self.clear_suggestions(user_id)
            self.user_choices[user_id]["choices_made"] = {}
            self.create_new_run(user_id, db_session, user_session)

        # Save current choice
        self.user_choices[user_id]["choices_made"]["current_choice"] = current_choice
        self.user_choices[user_id]["choices_made"][current_choice] = user_choice

        curr_prompt = self.QUESTIONS[current_choice]["model_prompt"]
        # prompt_to_use = curr_prompt
        if callable(curr_prompt):
            curr_prompt = curr_prompt(user_id, db_session, user_session, app)

        #removed stuff here

        else:
            self.update_conversation(
                user_id,
                "Model:{} \nUser:{} \n".format(curr_prompt, user_choice),
                db_session,
                app,
            )

        # Case: update suggestions for next attempt by removing relevant one
        if (
            current_choice == "suggestions"
        ):

            # PRE: user_choice is a string representing a number from 1-20,
            # or the title for the corresponding protocol

            try:
                current_protocol = self.TITLE_TO_PROTOCOL[user_choice]
            except KeyError:
                current_protocol = int(user_choice)

            protocol_chosen = Protocol(
                protocol_chosen=current_protocol,
                user_id=user_id,
                session_id=user_session.id,
                run_id=self.current_run_ids[user_id],
            )
            db_session.add(protocol_chosen)
            db_session.commit()
            self.current_protocol_ids[user_id] = [current_protocol, protocol_chosen.id]

            for i in range(len(self.suggestions[user_id])):
                curr_protocols = self.suggestions[user_id][i]
                if curr_protocols[0] == self.PROTOCOL_TITLES[current_protocol]:
                    curr_protocols.popleft()
                    if len(curr_protocols) == 0:
                        self.suggestions[user_id].pop(i)
                    break
        
        # TODO: use protocols for this from QUESTIONS
        # PRE: User choice is string in ["Better", "Worse"]
        # TODO: change here for recording insights on protocols
        # 'protocol' table changed to 'protocol_use'
        elif current_choice == "user_found_useful":
            current_protocol = Protocol.query.filter_by(
                id=self.current_protocol_ids[user_id][1]
            ).first()
            current_protocol.protocol_was_useful = user_choice
            db_session.commit()

        if current_choice == "guess_emotion":
            option_chosen = user_choice + " ({})".format(
                self.guess_emotion_predictions[user_id]
            )
        else:
            option_chosen = user_choice
        choice_made = Choice(
            choice_desc=current_choice,
            option_chosen=option_chosen,
            user_id=user_id,
            session_id=user_session.id,
            run_id=self.current_run_ids[user_id],
        )
        db_session.add(choice_made)
        db_session.commit()

        return choice_made

    def determine_next_choice(
        self, user_id, input_type, user_choice, db_session, user_session, app
    ):
        # Find relevant user info by using user_id as key in dict.
        #
        # Then using the current choice and user input, we determine what the next
        # choice is and return this as the output.

        # Some edge cases to consider based on the different types of each field:
        # May need to return list of model responses. For next protocol, may need
        # to call function if callable.

        # If we cannot find the specific choice (or if None etc.) can set user_choice
        # to "any".

        # PRE: Will be defined by save_current_choice if it did not already exist.
        # (so cannot be None)

        current_choice = self.user_choices[user_id]["choices_made"]["current_choice"]
        current_choice_for_question = self.QUESTIONS[current_choice]["choices"]
        # list of protocols for all choices
        current_protocols = self.QUESTIONS[current_choice]["protocols"]
        print("current_protocols: ", current_protocols)
        if input_type != "open_text":
            if (
                current_choice != "suggestions"
                and current_choice != "event_is_recent"
                and current_choice != "more_questions"
                #and current_choice != "after_classification_positive"

                and current_choice != "user_found_useful"
                and current_choice != "check_emotion"
                and current_choice != "new_protocol_better"
                and current_choice != "new_protocol_worse"
                and current_choice != "new_protocol_same"
                and current_choice != "choose_persona"
                and current_choice != "project_emotion"
                #and current_choice != "after_classification_negative"
                
                # Added these
                and current_choice != "pre_laughter_pos" 
                and current_choice != "explore_trigger_yes"
                and current_choice != "recommend_playful_protocol"
                and current_choice != "ask_feel_post_sg"
                and current_choice != "propose_sg_and_eg"
                and current_choice != "ask_incongruity"
                and current_choice != "ask_feel_pre_cv"
                and current_choice != "ask_feel_post_lb"
                #and current_choice != "encourage_feigning_laughter"
                and current_choice != "ask_feel_post_error"
                and current_choice != "ask_feel_pre_error"
                and current_choice != "continue_explaining_laughter_error"
                and current_choice != "continue_exploring_error"
                and current_choice != "ask_feel_post_setback"
                and current_choice != "encourage_laughter_setback" 
                and current_choice != "ask_feel_post_hardship"
                and current_choice != "remind_contempt_post_hardship"
                and current_choice != "encourage_laughter_hardship"
                and current_choice != "ask_feigning_laughter"
                and current_choice != "try_pre_lb"
                and current_choice != "encourage_try_lb"
                and current_choice != "ask_try_pre_setback"
                and current_choice != "ask_hardship"
                and current_choice != "ask_try_pre_hardship"
                and current_choice != "remind_contempt_post_protocol"
                and current_choice != "remind_contempt_pre_protocol"
                and current_choice != "ask_incongruity_and_cv"
                and current_choice != "covered_all_sessions"
                and current_choice != "choose_any"
                and current_choice != "final_feeling_check"
                and current_choice != "ending_neg"
                and current_choice != "ending_better"
                and current_choice != "remind_contempt_pre_laughter"
                and current_choice != "further_clarify_cv"
                and current_choice != "remind_contempt_post_error"
                and current_choice != "remind_contempt_pre_error"
                and current_choice != "remind_contempt_post_setback"
                and current_choice != "give_quote_setback"
                and current_choice != "give_quote_hardship"
                and current_choice != "remind_contempt_pre_setback"
                and current_choice != "remind_contempt_pre_hardship"
                and current_choice != "no_error"
                and current_choice != "ask_feel_pre_incongruity"
                and current_choice != "no_incongruity_cv"
                and current_choice != "constant_practice"
                and current_choice != "get_started"
                and current_choice != "review_any_session"
                and current_choice != "inform_playful"
                and current_choice != "reminder_incongruity"
                and current_choice != "ending_session_initial_pos"
            ):
                user_choice = user_choice.lower()
                # TODO: remove this annd all print statements
                # yes or no (positive or negative, etc.)
                print("user_choice: ", user_choice)

             # update emotional state
            if current_choice == "ask_present_feeling":
                self.user_states[user_id] = user_choice

            # update user's tiny session info
            if current_choice in self.TINY_SESSION_QUESTIONS:
                print("current_choice in self.TINY_SESSION_QUESTIONS")
                current_tiny_session_title = self.QUESTION_TO_TINY_SESSION[current_choice]
                self.user_tiny_sessions[user_id] = current_tiny_session_title
                #TODO
                #next_choice = 
                if len(self.user_covered_sessions[user_id]) == 0:
                    self.user_covered_sessions[user_id] = [current_tiny_session_title]
                else:
                    self.user_covered_sessions[user_id].append(current_tiny_session_title) 
                print("self.user_covered_sessions: ", self.user_covered_sessions)
            
            #ADDED THISE-------------
            if current_choice in self.NEGATIVE_TINY_SESSION_QUESTIONS:
                current_tiny_session_title = self.QUESTION_TO_NEGATIVE_TINY_SESSION[current_choice]
                self.user_tiny_sessions[user_id] = current_tiny_session_title
                # TODO:
                #next_choice = 
                if len(self.user_covered_sessions[user_id]) == 0:
                    self.user_covered_sessions[user_id] = [current_tiny_session_title]
                else:
                    self.user_covered_sessions[user_id].append(current_tiny_session_title) 
            #UP TO HERE-------------
        
            if (
                current_choice == "suggestions"
            ):
                try:
                    current_protocol = self.TITLE_TO_PROTOCOL[user_choice]
                except KeyError:
                    current_protocol = int(user_choice)
                protocol_choice = self.PROTOCOL_TITLES[current_protocol]
                next_choice = current_choice_for_question[protocol_choice]
                protocols_chosen = current_protocols[protocol_choice]

            elif current_choice == "check_emotion":
                if user_choice == "Sad":
                    next_choice = current_choice_for_question["Sad"]
                    protocols_chosen = current_protocols["Sad"]
                elif user_choice == "Angry":
                    next_choice = current_choice_for_question["Angry"]
                    protocols_chosen = current_protocols["Angry"]
                elif user_choice == "Anxious/Scared":
                    next_choice = current_choice_for_question["Anxious/Scared"]
                    protocols_chosen = current_protocols["Anxious/Scared"]
                else:
                    next_choice = current_choice_for_question["Happy/Content"]
                    protocols_chosen = current_protocols["Happy/Content"]
            else:
                # TODO: remove print:
                # next_choice is the next question name (in QUESTIONS)
                next_choice = current_choice_for_question[user_choice]
                print("next_choice: ", next_choice)
                # protocols_chosen is a list of protocols, i.e. ['3: Self-glory', '7: Contrasting views']
                protocols_chosen = current_protocols[user_choice]
                print("protocols_chosen: ", protocols_chosen)

        else:
            next_choice = current_choice_for_question["open_text"]
            protocols_chosen = current_protocols["open_text"]

        if callable(next_choice):
            next_choice = next_choice(user_id, db_session, user_session, app)

        if current_choice == "guess_emotion" and user_choice.lower() == "yes": #TODO
            if self.guess_emotion_predictions[user_id] == "Sad":
                next_choice = next_choice["Sad"]
            elif self.guess_emotion_predictions[user_id] == "Angry":
                next_choice = next_choice["Angry"]
            elif self.guess_emotion_predictions[user_id] == "Anxious/Scared":
                next_choice = next_choice["Anxious/Scared"]
            else:
                next_choice = next_choice["Happy/Content"]

        # TODO: remove print statements
        if callable(protocols_chosen):
            protocols_chosen = protocols_chosen(user_id, db_session, user_session, app)
            print("protocols_chosen are callable and = ", protocols_chosen)
        else:
            print("protocols_chosen are NOT callable")
        next_prompt = self.QUESTIONS[next_choice]["model_prompt"]
        if callable(next_prompt):
            next_prompt = next_prompt(user_id, db_session, user_session, app)
        if (
            len(protocols_chosen) > 0
            and current_choice != "suggestions"
        ):
            self.update_suggestions(user_id, protocols_chosen, app)

        # Case: new suggestions being created after first protocol attempted
        if next_choice == "opening_prompt":
            self.clear_suggestions(user_id)
            self.clear_emotion_scores(user_id)
            self.create_new_run(user_id, db_session, user_session)

        if next_choice == "suggestions":
            next_choices = self.get_suggestions(user_id, app)

        else:
            next_choices = list(self.QUESTIONS[next_choice]["choices"].keys())
        self.user_choices[user_id]["choices_made"]["current_choice"] = next_choice
        return {"model_prompt": next_prompt, "choices": next_choices}
