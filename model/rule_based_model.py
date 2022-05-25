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
from model.classifiers import get_emotion, fluency_score, get_sentence_score, get_sentence_score_new, empathy_score, get_humour_scores
from model.utterances import *
from model.questions_main import *
from model.questions_reused import *
from model.questions_negative import *
from model.questions_positive import *
from model.questions_mini_session import *

nltk.download("wordnet")
from nltk.corpus import wordnet  # noqa

class ModelDecisionMaker:
    def __init__(self):

        # removed personas
        self.kai = pd.read_csv('/Users/zeenapatel/dev/HumBERT/model/kai.csv', encoding='ISO-8859-1') # changed path
        self.dataset = pd.read_csv('/Users/zeenapatel/dev/HumBERT/model/humbert_statements.csv', encoding='ISO-8859-1') # changed path

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
            ("3: Self-glory",), 
            ("4: Incongruous world", "5: Incongruous self", "6: Self/world incongruity"), 
            ("7: Contrasting views",), 
            ("8: Our own laughter brand", "9: Feigning laughter"), 
            ("10: Self-laughter",), 
            ("11: Laughing at misfortunes and disturbing circumstances",), 
            ("12: Laughing at long-term suffering",)
        ]

        self.MINI_SESSION_TITLE_TO_LEVEL = dict(zip(self.MINI_SESSION_TITLES, [0, 0, 1, 1, 1, 2, 3, 3]))

        #TODO add not_haha? - change random choice to 1/16 - not haha and 1/16 - haha
        self.MINI_SESSION_QUESTIONS = ["ask_playful_mode_no_haha", "ask_self_glory_not_haha", "ask_incongruity", "ask_feel_pre_cv", "ask_laughter_brand", "ask_recent_error", "ask_setback", "ask_hardship"]

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
    
    def pre_compute_empathy_scores(self):
        data = pd.read_csv('/Users/zeenapatel/dev/HumBERT/model/scored_statements.csv', encoding='ISO-8859-1')
        empathy_scores = []
        if 'empathy' not in data.columns:
            for row in data['sentences'].dropna():
                score = empathy_score(row)
                print('score is: ', score)
                empathy_scores.append(score)
            data['empathy'] = empathy_scores
            data.to_csv('/Users/zeenapatel/dev/HumBERT/model/scored_statements.csv')

    def pre_compute_fluency_scores(self):
        data = pd.read_csv('/Users/zeenapatel/dev/HumBERT/model/scored_statements.csv', encoding='ISO-8859-1')
        fluency_scores = []
        if 'fluency' not in data.columns:
            for row in data['sentences'].dropna():
                score = fluency_score(row)
                print('score is: ', score)
                fluency_scores.append(score)
            data['fluency'] = fluency_scores
            data.to_csv('/Users/zeenapatel/dev/HumBERT/model/scored_statements.csv')

    def pre_compute_humour_scores(self):
        data = pd.read_csv('/Users/zeenapatel/dev/HumBERT/model/scored_statements.csv', encoding='ISO-8859-1')
        if 'humour' not in data.columns:
            humour_scores = get_humour_scores(data)
            data['humour'] = pd.Series(humour_scores)
            data.to_csv('/Users/zeenapatel/dev/HumBERT/model/scored_statements.csv')
        else:
            print('humour scores calculated!')


    def initialise_remaining_choices(self, user_id):
        self.remaining_choices[user_id] = ["displaying_antisocial_behaviour", "internal_persecutor_saviour", "personal_crisis", "rigid_thought"]
    
    def initialise_user_session_vars(self, user_id):
        # TODO: FOR NOW!!!!!!!
        # drop negative once done (from list!)
        self.user_mini_sessions[user_id] = ("1: Playful mind", "2: Playful face")
        self.user_covered_sessions[user_id] = []
        self.contempt_message[user_id] = False
        self.covered_all_message[user_id] = False
        self.haha_count[user_id] = 0
    
    def check_acknowledge_achievements(self, user_id):
        if ('3: Self-glory',) in self.user_covered_sessions[user_id]: 
            return "continue_curr_can't_do" 
        # TODO
        return "ask_self_glory_haha"

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

    def get_review_prompt(self, user_id):
        #prev_qs = pd.DataFrame(self.recent_questions[user_id],columns=['sentences'])
            data = self.dataset
            base_prompt = "Great. Just to let you know, they are also being displayed on the right of the screen in my browser view.*Feel free to review them at any point in our conversation."
            column = data[base_prompt].dropna()
            #question = self.get_best_sentence(column, prev_qs)
            question = np.random.choice(column)
            get_sentence_score_new(question, self.dataset)
            not_perfect = '\u0336'.join("perfect") + '\u0336'
            phrases = ["ah, ah, ah, ah, ...", "eh, eh, eh, eh, ...", "ih, ih, ih, ih, ...", "oh, oh, oh, oh, ...", "uh, uh, uh, uh, ..."]
            nl = '\n'
            laughter = "ah, ah, ah, ah, ..., eh, eh, eh, eh, ..., oh, oh, oh, oh, ..., ih, ih, ih, ih, ih, ..., uh, uh, uh, uh, ..."
            second_laughter = "\"ah, ah, ah, ah, ...\", \"eh, eh, eh, eh, ...\", \"oh, oh, oh, oh, ...\", \"ih, ih, ih, ih, ih, ...\", \"uh, uh, uh, uh, ...\"."
            question = question.format(second_laughter).split("*")
            return question
            #if len(self.recent_questions[user_id]) < 50:
            #    self.recent_questions[user_id].append(question)
            #else:
            #    self.recent_questions[user_id] = []
            #    self.recent_questions[user_id].append(question)
            #return self.split_sentence(question)

    def get_restart_prompt(self, user_id):
        #TODO: why time.sleep()
        time.sleep(7)
        if self.users_names[user_id] == "":
            restart_prompt = ["Please tell me again, how are you feeling today?"]
        else:
            restart_prompt = ["Please tell me again, " + self.users_names[user_id] + ", how are you feeling today?"]
        return restart_prompt
    
    # TODO added (right place)
    #def choose_mini_session(self, user_id): 
    #from user_id: current emotional state, current protocol/level, previous protocols 
    # state can be "Positive" (Better), "Negative" (Worse) or "Neutral" (Same) 
    def determine_next_mini_session(self, user_id, state):
        sessions_left = list(set(self.MINI_SESSION_TITLES) - set(self.user_covered_sessions[user_id]))
        print("self.user_covered_sessions: ", self.user_covered_sessions)
        print("sessions_left: ", sessions_left)
        next_session_options = set() #random non recent if no options or if user's finnished all - suggest they chooose

        current_state = self.user_states[user_id]
        current_session = self.user_mini_sessions[user_id]
        print("current_session: ", current_session)
        current_level = self.MINI_SESSION_TITLE_TO_LEVEL[current_session]

        if len(sessions_left) > 0:
            sorted_sessions = sorted(sessions_left,key=self.MINI_SESSION_TITLES.index)
            min_session_level = self.MINI_SESSION_TITLE_TO_LEVEL[sorted_sessions[0]]

            print("sorted sessions: ", sorted_sessions)
            print("min_session_level: ", min_session_level)
            for session in sessions_left:
                session_level = self.MINI_SESSION_TITLE_TO_LEVEL[session]
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
            # covered all mini sessions
            if self.covered_all_message:
                return "review_any_session"
            else:
                self.covered_all_message = True
                return "covered_all_sessions"
        if next_session_options == set():
            print("THERE ARE NO next_session_options")
            random_choice = random.sample(sessions_left, 1)
            next_session_options.add(tuple(random_choice)[0])
            #next_session_options.add(np.random.choice(sessions_left))

        random_choice = random.sample(next_session_options, 1)
        return self.MINI_SESSION_TO_QUESTION[tuple(random_choice)[0]]
        return self.MINI_SESSION_TO_QUESTION[np.random.choice(next_session_options)]

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

    def get_best_sentence_new(self, column, prev_qs):
        #return random.choice(column.dropna().sample(n=15).to_list()) #using random choice instead of machine learning
        maxscore = 0
        chosen = ''
        if not greeting in column.unique():
            for row in column.dropna().sample(n=10): #was 25 #TODO CHANGE - 12?
                fitscore = get_sentence_score_new(row, prev_qs)
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
                #and current_choice != "recommend_playful_protocol" #smileysss
                and current_choice != "ask_feel_post_sg"
                #and current_choice != "propose_sg_and_eg" #smileysss
                and current_choice != "ask_incongruity"
                #and current_choice != "ask_feel_pre_cv" #smileysss
                and current_choice != "ask_feel_post_lb"
                #and current_choice != "encourage_feigning_laughter"
                and current_choice != "ask_feel_post_error"
                #and current_choice != "ask_feel_pre_error" #smileysss
                #and current_choice != "continue_explaining_laughter_error" #smileysss
                #and current_choice != "continue_exploring_error" #smileysss
                and current_choice != "ask_feel_post_setback"
                #and current_choice != "encourage_laughter_setback" #smileysss
                and current_choice != "ask_feel_post_hardship"
                and current_choice != "remind_contempt_post_hardship"
                #and current_choice != "encourage_laughter_hardship" #smileysss
                #and current_choice != "ask_feigning_laughter" #smileysss
                and current_choice != "try_pre_lb_haha"
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
                and current_choice != "further_clarify_cv_not_haha"
                and current_choice != "further_clarify_cv_haha"
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
                #and current_choice != "funny_no_error"
                #and current_choice != "not_funny_no_error"
                #and current_choice != "ask_feel_pre_incongruity" #smileys
                #and current_choice != "no_incongruity_cv" #smileys
                and current_choice != "no_incongruity_cv_haha"
                and current_choice != "constant_practice_haha"
                and current_choice != "get_started"
                and current_choice != "review_any_session"
                and current_choice != "inform_playful"
                and current_choice != "reminder_incongruity"
                and current_choice != "ending_session_initial_pos"
                and current_choice != "guess_emotion"
                and current_choice != "ask_emotion_haha"
                and current_choice != "funny_ending"
                and current_choice != "not_funny_ending"
                #and current_choice != "funny_playful"
                #and current_choice != "not_funny_playful"
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
                and current_choice != "trigger_not_hardship_haha"
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
            ):
                user_choice = user_choice.lower()
                # TODO: remove this annd all print statements
                # yes or no (positive or negative, etc.)
                print("user_choice: ", user_choice)

             # update emotional state
            if current_choice == "ask_present_feeling":
                self.user_states[user_id] = user_choice

            # update user's mini session info
            if current_choice in self.MINI_SESSION_QUESTIONS:
                print("current_choice in self.MINI_SESSION_QUESTIONS")
                current_mini_session_title = self.QUESTION_TO_MINI_SESSION[current_choice]
                self.user_mini_sessions[user_id] = current_mini_session_title
                #TODO
                #next_choice = 
                if len(self.user_covered_sessions[user_id]) == 0:
                    self.user_covered_sessions[user_id] = [current_mini_session_title]
                else:
                    self.user_covered_sessions[user_id].append(current_mini_session_title) 
                print("self.user_covered_sessions: ", self.user_covered_sessions)
            
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
                print("next_choice: ", next_choice)
                # protocols_chosen is a list of protocols, i.e. ['3: Self-glory', '7: Contrasting views']
                protocols_chosen = current_protocols[user_choice]
                print("protocols_chosen: ", protocols_chosen)

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
