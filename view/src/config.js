// Config starter code
import React from "react";
import { createChatBotMessage } from "react-chatbot-kit";

import YesNoOptions from "./widgets/options/GeneralOptions/YesNoOptions";
import ProtocolOptions from "./widgets/options/GeneralOptions/ProtocolOptions";
import ContinueOptions from "./widgets/options/GeneralOptions/ContinueOptions";
import FeedbackOptions from "./widgets/options/GeneralOptions/FeedbackOptions";
import EmotionOptions from "./widgets/options/GeneralOptions/EmotionOptions";
import EventOptions from "./widgets/options/GeneralOptions/EventOptions";
import YesNoProtocolOptions from "./widgets/options/GeneralOptions/YesNoProtocolsOptions";
import FeelingOptions from "./widgets/options/GeneralOptions/FeelingOptions";
import FeelingOptions2 from "./widgets/options/GeneralOptions/FeelingOptions2";

const botName = "HumBERT";

const config = {
  botName: botName,
  initialMessages: [
    createChatBotMessage("Please enter your username:", {
      withAvatar: true,
      delay: 50,
    }),
  ],

  state: {
    userState: null,
    username: null,
    password: null,
    sessionID: null,
    protocols: [],
    askingForProtocol: false
  },
  customComponents: {
    header: () => <div style={{
      height: '16px', fontFamily: 'Arial', borderTopLeftRadius: '5px', borderTopRightRadius: '5px',
      background: '#EBECED', color: '#4A4A4A', padding: '8px', borderBottom: '1px solid #B8BABA'
    }}>Conversation</div>,
    botAvatar: () => <div class="react-chatbot-kit-chat-bot-avatar-container" style={{ fontFamily: 'Arial' }}><p class="react-chatbot-kit-chat-bot-avatar-letter">S</p></div>
  },

  widgets: [
    {
      widgetName: "YesNo",
      widgetFunc: (props) => <YesNoOptions {...props} />,
      mapStateToProps: ["userState", "sessionID"],
    },
    {
      widgetName: "Continue",
      widgetFunc: (props) => <ContinueOptions {...props} />,
      mapStateToProps: ["userState", "sessionID"],
    },
    {
      widgetName: "Emotion",
      widgetFunc: (props) => <EmotionOptions {...props} />,
      mapStateToProps: ["userState", "sessionID"],
    },
    {
      widgetName: "Feedback",
      widgetFunc: (props) => <FeedbackOptions {...props} />,
      mapStateToProps: ["userState", "sessionID"],
    },
    {
      widgetName: "Protocol",
      widgetFunc: (props) => <ProtocolOptions {...props} />,
      mapStateToProps: ["userState", "sessionID", "protocols", "askingForProtocol"],
    },
    {
      widgetName: "YesNoProtocols",
      widgetFunc: (props) => <YesNoProtocolOptions {...props} />,
      mapStateToProps: ["userState", "sessionID"],
    },
    {
      widgetName: "RecentDistant",
      widgetFunc: (props) => <EventOptions {...props} />,
      mapStateToProps: ["userState", "sessionID"],
    },
    {
      widgetName: "Feeling",
      widgetFunc: (props) => <FeelingOptions {...props} />,
      mapStateToProps: ["userState", "sessionID"],
    },
    {
      widgetName: "Feeling2",
      widgetFunc: (props) => <FeelingOptions2 {...props} />,
      mapStateToProps: ["userState", "sessionID"],
    },
  ],
};

export default config;
