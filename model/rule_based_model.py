import string
import nltk

import pandas as pd
import numpy as np
import random
from collections import deque
import re
import datetime
import time

from model.models import UserModelSession, Choice, UserModelRun, Protocol
from model.classifiers import get_emotion, fluency_score, get_sentence_score, get_sentence_score_pos, get_sentence_score_neg, empathy_score, get_humour_scores
from model.utterances import *
from model.questions_main import get_main_questions
from model.questions_reused import get_reused_questions
from model.questions_negative import get_negative_questions
from model.questions_positive import get_positive_questions
from model.questions_mini_session import get_mini_sessions_questions

nltk.download("wordnet")
from nltk.corpus import wordnet  # noqa

class ModelDecisionMaker:
    def __init__(self):

        self.dataset = pd.read_csv('/Users/zeenapatel/dev/HumBERT/model/humbert_statements.csv', encoding='ISO-8859-1')
        self.scored_statements = pd.read_csv('/Users/zeenapatel/dev/HumBERT/model/scored_statements.csv', encoding='ISO-8859-1')

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

        self.MINI_SESSION_TITLES = [
            ("1: Playful mind", "2: Playful face"), 
            ("1: Playful mind", "2: Playful face"),
            ("3: Self-glory",),
            ("3: Self-glory",),  
            ("4: Incongruous world", "5: Incongruous self", "6: Self/world incongruity"), 
            ("7: Contrasting views",), 
            ("8: Our own laughter brand", "9: Feigning laughter"), 
            ("10: Self-laughter",), 
            ("11: Laughing at misfortunes and disturbing circumstances",), 
            ("12: Laughing at long-term suffering",)
        ]

        self.MINI_SESSION_TITLE_TO_LEVEL = dict(zip(self.MINI_SESSION_TITLES, [0, 0, 0, 0, 1, 1, 1, 2, 3, 3]))

        #TODO add not_haha? - change random choice to 1/16 - not haha and 1/16 - haha
        #self.MINI_SESSION_QUESTIONS = ["ask_playful_mode_no_haha", "ask_self_glory_not_haha", "ask_incongruity", "ask_feel_pre_cv", "ask_laughter_brand", "ask_recent_error", "ask_setback", "ask_hardship"]
        self.MINI_SESSION_QUESTIONS = ["ask_playful_mode_no_haha", "ask_playful_mode_haha", "ask_self_glory_not_haha", "ask_self_glory_haha", "ask_incongruity", "ask_feel_pre_cv", "ask_laughter_brand", "ask_recent_error", "ask_setback", "ask_hardship"]
        self.MINI_SESSION_TO_QUESTION = dict(zip(self.MINI_SESSION_TITLES, self.MINI_SESSION_QUESTIONS))
        self.QUESTION_TO_MINI_SESSION = dict(zip(self.MINI_SESSION_QUESTIONS, self.MINI_SESSION_TITLES))

        #TODO: check if we need self.NEGATIVE_MINI_SESSION_TITLES, QUESTIONS, self.PROTOCOL_MINI_SESSIONS,etc.

        self.NEGATIVE_MINI_SESSION_TITLES = [
            ("4: Incongruous world", "5: Incongruous self", "6: Self/world incongruity"), 
            ("10: Self-laughter",), 
            ("11: Laughing at misfortunes and disturbing circumstances",), 
            ("12: Laughing at long-term suffering",)
        ]
        self.NEGATIVE_MINI_SESSION_TITLE_TO_LEVEL = dict(zip(self.NEGATIVE_MINI_SESSION_TITLES, [1, 2, 3, 3]))
        self.NEGATIVE_MINI_SESSION_QUESTIONS = ["ask_laughter_incongruity", "ask_feel_pre_error", "ask_laughter_setback", "ask_accept_hardship_no_haha"]
        self.NEGATIVE_MINI_SESSION_TO_QUESTION = dict(zip(self.NEGATIVE_MINI_SESSION_TITLES, self.NEGATIVE_MINI_SESSION_QUESTIONS))
        self.QUESTION_TO_NEGATIVE_MINI_SESSION = dict(zip(self.NEGATIVE_MINI_SESSION_QUESTIONS, self.NEGATIVE_MINI_SESSION_TITLES))

        # Stores the initial emotional state of each user after they classify it (positive or negative)
        self.user_states_initial = {}
        # Tracks the current emotional state of each user (positive or negative)
        self.user_states = {}
        # Tracks the feeling of each user before or aftter attempting the current protocol (positive & negative or better, worse & same)
        # keys: user ids, values: string tuples: (pre/post, feeling)
        self.user_protocol_feelings = {}
        # Tracks each user's current mini session (including None)
        self.user_mini_sessions = {}
        # Tracks the mini sessions covered by each user so far 
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
        
        # Tracks whether each user has received the covered-all-sessions message 
        self.covered_all_message = {}

        # Tracks the number of times each user has responded to the chatbot's joke 
        self.haha_count = {}
        
        self.guess_emotion_predictions = {}

        self.users_names = {}
        self.remaining_choices = {}

        self.recent_questions = {}
        self.recent_statements = {}

        #self.chosen_personas = {}
        #self.datasets = {}

        # Structure of dictionary: {question: {
        #                           model_prompt: str or list[str],
        #                           choices: {maps user response to next protocol},
        #                           protocols: {maps user response to protocols to suggest},
        #                           }, ...
        #                           }
        # This could be adapted to be part of a JSON file (would need to address
        # mapping callable functions over for parsing).

        self.QUESTIONS_MAIN = get_main_questions(self)
        self.QUESTIONS_REUSED = get_reused_questions(self)
        self.QUESTIONS_MINI_SESSIONS = get_mini_sessions_questions(self)
        self.QUESTIONS_POSITIVE = get_positive_questions(self)
        self.QUESTIONS_NEGATIVE = get_negative_questions(self)

        self.QUESTIONS = {**self.QUESTIONS_MAIN , **self.QUESTIONS_REUSED, **self.QUESTIONS_MINI_SESSIONS, **self.QUESTIONS_POSITIVE, **self.QUESTIONS_NEGATIVE}
        self.QUESTION_KEYS = list(self.QUESTIONS.keys())
    
    def initialise_prev_questions(self, user_id):
        self.recent_questions[user_id] = []
        self.recent_statements[user_id] = []

    def clear_persona(self, user_id):
        self.chosen_personas[user_id] = ""

    def clear_names(self, user_id):
        self.users_names[user_id] = ""

    def clear_datasets(self, user_id):
        self.datasets[user_id] = pd.DataFrame(columns=['sentences'])
    
    def pre_compute_scores(self):
        self.pre_compute_fluency_scores()
        self.pre_compute_humour_scores()
        self.pre_compute_empathy_scores()
    
    def pre_compute_empathy_scores(self):
        #data = pd.read_csv('/Users/zeenapatel/dev/HumBERT/model/scored_statements.csv', encoding='ISO-8859-1')
        data = self.scored_statements
        empathy_scores = []
        if 'empathy' not in data.columns:
            for row in data['sentences'].dropna():
                score = empathy_score(row)
                empathy_scores.append(score)
            data['empathy'] = empathy_scores
            data.to_csv('/Users/zeenapatel/dev/HumBERT/model/scored_statements.csv')

    def pre_compute_fluency_scores(self):
        data = self.scored_statements
        fluency_scores = []
        if 'fluency' not in data.columns:
            for row in data['sentences'].dropna():
                score = fluency_score(row)
                fluency_scores.append(score)
            data['fluency'] = fluency_scores
            data.to_csv('/Users/zeenapatel/dev/HumBERT/model/scored_statements.csv')

    def pre_compute_humour_scores(self):
        data = self.scored_statements
        if 'humour' not in data.columns:
            humour_scores = get_humour_scores(data)
            data['humour'] = pd.Series(humour_scores)
            data.to_csv('/Users/zeenapatel/dev/HumBERT/model/scored_statements.csv')

    def initialise_remaining_choices(self, user_id):
        self.remaining_choices[user_id] = ["displaying_antisocial_behaviour", "internal_persecutor_saviour", "personal_crisis", "rigid_thought"]
    
    def initialise_user_session_vars(self, user_id):
        # TODO: FOR NOW!!!!!!!
        # drop negative once done (from list!)
        self.user_states_initial[user_id] = "Positive"
        self.user_mini_sessions[user_id] = ("1: Playful mind", "2: Playful face")
        self.user_covered_sessions[user_id] = []
        self.contempt_message[user_id] = False
        self.covered_all_message[user_id] = False
        self.haha_count[user_id] = 0
    
    def check_acknowledge_achievements(self, user_id):
        if ('3: Self-glory',) in self.user_covered_sessions[user_id]: 
            return "continue_curr_can't_do" 
        # TODO
        return self.determine_next_prompt_haha("ask_self_glory_haha", "ask_self_glory_not_haha")

    def check_contempt(self, user_id):
        if self.contempt_message[user_id] == False: 
            self.contempt_message[user_id] = True
            return "remind_contempt_pre_laughter" 
        return "encourage_laughter"

    def check_contempt_pre(self, user_id):
        if self.contempt_message[user_id] == False: 
            self.contempt_message[user_id] = True
            return "remind_contempt_pre_protocol_haha" 
        else: return "continue_curr_not_willing"
    
    def check_contempt_post(self, user_id):
        if self.contempt_message[user_id] == False: 
            self.contempt_message[user_id] = True
            return "remind_contempt_post_protocol"
        else: return "try_post_protocol_neg"
    
    def check_contempt_post_error(self, user_id):
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

    # used to determine an optimal fitness score (for positive and negative scenarios)
    def test_retrieval_function(self):
        df = pd.read_csv('/Users/zeenapatel/Desktop/datasets/testing_pos_retrieval_function.csv', encoding='ISO-8859-1')
        #df = pd.read_csv('/Users/zeenapatel/Desktop/datasets/testing_neg_retrieval_function.csv', encoding='ISO-8859-1')
        #print('started testing retrieval function...')
        column_statements = []
        for column in self.dataset:
            previous_questions = pd.DataFrame(columns=['sentences']) # start with an empty dataframe which is gradually filled with the retrieved utterances
            for _ in range(30): # we retrieve 20 utterances here
                maxscore = 0
                chosen = ''
                for row in self.dataset[column].dropna():  # select a column/base utterance we want to retrieve the variations of
                    if pd.notna(row):
                        fitscore = get_sentence_score_pos(row, previous_questions)
                        #fitscore = get_sentence_score_neg(row, previous_questions)
                        if fitscore > maxscore:
                            maxscore = fitscore
                            chosen = row
                column_statements.append(chosen)
                previous_questions = previous_questions.append({'sentences':chosen}, ignore_index=True)
            df[column] = column_statements
            df.to_csv('/Users/zeenapatel/Desktop/datasets/testing_pos_retrieval_function.csv')
            #df.to_csv('/Users/zeenapatel/Desktop/datasets/testing_neg_retrieval_function.csv')
            column_statements = []
        #print('finished testing retrieval function!')

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

        #print("self.suggestions[user_id]: ", self.suggestions[user_id])

    # Takes next item in queue, or moves on to suggestions
    # if all have been checked
    
    def get_restart_prompt(self, user_id):
        #TODO: why time.sleep()
        time.sleep(7)
        if self.users_names[user_id] == "":
            restart_prompt = ["Please tell me again, how are you feeling today?"]
        else:
            restart_prompt = ["Please tell me again, " + self.users_names[user_id] + ", how are you feeling today?"]
        return restart_prompt
    
    def determine_next_prompt_haha(self, question1, question2):
        return np.random.choice([question1, question2], 1, p=[0.35, 0.65])[0]
    
    # TODO added (right place)
    #def choose_mini_session(self, user_id): 
    #from user_id: current emotional state, current protocol/level, previous protocols 
    # state can be "Positive" (Better), "Negative" (Worse) or "Neutral" (Same) 
    def determine_next_mini_session(self, user_id, state):
        sessions_left = list(set(self.MINI_SESSION_TITLES) - set(self.user_covered_sessions[user_id]))
        #print("covered sessions: ", self.user_covered_sessions)
        #print("sessions_left: ", sessions_left)
        next_session_options = set() #random non recent if no options or if user's finnished all - suggest they chooose

        current_state = self.user_states[user_id]
        current_session = self.user_mini_sessions[user_id]
        #print("current_session: ", current_session)
        current_level = self.MINI_SESSION_TITLE_TO_LEVEL[current_session]

        if len(sessions_left) > 0:
            sorted_sessions = sorted(sessions_left,key=self.MINI_SESSION_TITLES.index)
            min_session_level = self.MINI_SESSION_TITLE_TO_LEVEL[sorted_sessions[0]]

            #print("sorted sessions: ", sorted_sessions)
            #print("min_session_level: ", min_session_level)
            for session in sessions_left:
                session_level = self.MINI_SESSION_TITLE_TO_LEVEL[session]
                #print("session_level: ", session_level)
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
                        if session_level <= current_level:
                            next_session_options.add(session)
                    elif state == "Negative":
                        if session_level == min_session_level:
                            next_session_options.add(session)
                    elif state == "Neutral":
                        if session_level <= current_level:
                            next_session_options.add(session)
        else:
            # covered all mini sessions
            if self.covered_all_message == True:
                return "review_any_session"
            else:
                self.covered_all_message = True
                return "covered_all_sessions"
        if next_session_options == set():
            #print("no next_session_options!")
            random_choice = random.sample(sessions_left, 1)
            next_session_options.add(tuple(random_choice)[0])

        random_choice = random.sample(next_session_options, 1)
        return self.MINI_SESSION_TO_QUESTION[tuple(random_choice)[0]]

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

    def get_best_sentence_new(self, column, prev_qs, user_id):
        maxscore = 0
        chosen = ''
        if not greeting in column.unique():
            for row in column.dropna().sample(n=10): #was 25 #TODO CHANGE - 12?
                if self.user_states_initial[user_id] == "Positive":
                    fitscore = get_sentence_score_pos(row, prev_qs)
                else:
                    fitscore = get_sentence_score_neg(row, prev_qs)
                if fitscore > maxscore:
                    maxscore = fitscore
                    chosen = row
            if chosen != '':
                return chosen
        return random.choice(column.dropna().to_list())#before was column.dropna().sample(n=5).to_list()) #was 25       

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
        #print("current_protocols: ", current_protocols)
        if input_type != "open_text":
            if (current_choice != "pre_laughter_pos" 
                and current_choice != "check_emotion"
                and current_choice != "explore_trigger_yes"
                and current_choice != "ask_feel_post_sg"
                and current_choice != "ask_incongruity"
                and current_choice != "ask_feel_post_lb"
                and current_choice != "ask_feel_post_error"
                and current_choice != "ask_feel_post_setback"
                and current_choice != "ask_feel_post_hardship"
                and current_choice != "remind_contempt_post_hardship"
                and current_choice != "encourage_try_lb"
                and current_choice != "ask_try_pre_setback"
                and current_choice != "ask_hardship"
                and current_choice != "ask_try_pre_hardship"
                and current_choice != "remind_contempt_post_protocol"
                and current_choice != "remind_contempt_pre_protocol_no_haha"
                and current_choice != "ask_incongruity_and_cv"
                and current_choice != "covered_all_sessions"
                and current_choice != "choose_any"
                and current_choice != "final_feeling_check"
                and current_choice != "ending_neg_haha"
                and current_choice != "ending_neg_no_haha"
                and current_choice != "ending_better_no_haha"
                and current_choice != "ending_better_haha"
                and current_choice != "remind_contempt_pre_laughter"
                and current_choice != "continue_cv_haha"
                and current_choice != "continue_cv_no_haha"
                and current_choice != "remind_contempt_post_error"
                and current_choice != "remind_contempt_pre_error"
                and current_choice != "remind_contempt_post_setback"
                and current_choice != "give_quote_setback"
                and current_choice != "give_quote_hardship"
                and current_choice != "remind_contempt_pre_setback"
                and current_choice != "remind_contempt_pre_hardship"
                and current_choice != "no_error_no_haha"
                and current_choice != "no_error_haha"
                and current_choice != "ask_relevant_context"
                and current_choice != "no_incongruity_cv_haha"
                and current_choice != "constant_practice_haha"
                and current_choice != "get_started"
                and current_choice != "review_any_session"
                and current_choice != "inform_playful"
                and current_choice != "ending_session_initial_pos"
                and current_choice != "guess_emotion"
                and current_choice != "ask_emotion_haha"
                and current_choice != "funny_ending"
                and current_choice != "not_funny_ending"
                and current_choice != "response_to_song_haha"
                and current_choice != "recommend_song_haha"
                and current_choice != "ask_self_glory_haha"
                and current_choice != "propose_congratulate_with_smile_haha"
                and current_choice != "clarify_laughter_haha"
                and current_choice != "further_clarify_fl_haha"
                and current_choice != "encourage_laughter_error_haha"
                and current_choice != "propose_reflect_setback_haha"
                and current_choice != "ask_accept_hardship_haha"
                and current_choice != "propose_reflect_hardship_haha"
                and current_choice != "continue_pos_pre_protocol_haha"
                and current_choice != "try_pre_protocol_pos_haha"
                and current_choice != "try_pre_protocol_neg_haha"
                and current_choice != "remind_contempt_pre_protocol_haha"
                and current_choice != "ask_laughter_incongruity_haha"
                and current_choice != "further_clarify_pre_error_haha"
                and current_choice != "further_clarify_post_error_haha"
                and current_choice != "encourage_laughter_setback_haha"
                and current_choice != "encourage_laughter_hardship_haha"
                and current_choice != "ask_playful_mode_haha"
                and current_choice != "recommend_review"
                and current_choice != "remind_review"
                and current_choice != "recommend_review_more_details"
            ):
                user_choice = user_choice.lower()
                # TODO: remove this annd all print statements
                # yes or no (positive or negative, etc.)
                #print("user_choice: ", user_choice)

             # update emotional state
            if current_choice == "ask_present_feeling":
                self.user_states[user_id] = user_choice

            # update user's mini session info
            if current_choice in self.MINI_SESSION_QUESTIONS:
                #print("current_choice is in self.MINI_SESSION_QUESTIONS")
                current_mini_session_title = self.QUESTION_TO_MINI_SESSION[current_choice]
                self.user_mini_sessions[user_id] = current_mini_session_title
                #TODO
                #next_choice = 
                if len(self.user_covered_sessions[user_id]) == 0:
                    self.user_covered_sessions[user_id] = [current_mini_session_title]
                else:
                    self.user_covered_sessions[user_id].append(current_mini_session_title) 
                #print("self.user_covered_sessions: ", self.user_covered_sessions)
            
            #ADDED THISE-------------
            if current_choice in self.NEGATIVE_MINI_SESSION_QUESTIONS:
                current_mini_session_title = self.QUESTION_TO_NEGATIVE_MINI_SESSION[current_choice]
                self.user_mini_sessions[user_id] = current_mini_session_title
                # TODO:
                #next_choice = 
                if len(self.user_covered_sessions[user_id]) == 0:
                    self.user_covered_sessions[user_id] = [current_mini_session_title]
                else:
                    self.user_covered_sessions[user_id].append(current_mini_session_title) 
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
                #print("next_choice: ", next_choice)
                # protocols_chosen is a list of protocols, i.e. ['3: Self-glory', '7: Contrasting views']
                protocols_chosen = current_protocols[user_choice]
                #print("protocols_chosen: ", protocols_chosen)

        else:
            next_choice = current_choice_for_question["open_text"]
            protocols_chosen = current_protocols["open_text"]

        if callable(next_choice):
            next_choice = next_choice(user_id, db_session, user_session, app)

        if current_choice == "guess_emotion" and user_choice.lower() == "that's correct": #TODO
            if self.guess_emotion_predictions[user_id] == "Sad":
                next_choice = next_choice["Sad"]
            elif self.guess_emotion_predictions[user_id] == "Angry":
                next_choice = next_choice["Angry"]
            elif self.guess_emotion_predictions[user_id] == "Anxious/Scared":
                next_choice = next_choice["Anxious/Scared"]
            else:
                next_choice = next_choice["Happy/Content"]

        if callable(protocols_chosen):
            protocols_chosen = protocols_chosen(user_id, db_session, user_session, app)
            #print("protocols_chosen are callable and = ", protocols_chosen)
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

        next_choices = list(self.QUESTIONS[next_choice]["choices"].keys())
        self.user_choices[user_id]["choices_made"]["current_choice"] = next_choice
        return {"model_prompt": next_prompt, "choices": next_choices}
