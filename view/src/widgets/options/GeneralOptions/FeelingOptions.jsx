import React from "react";
import Options from "../Options/Options";

const FeelingOptions = (props) => {
  const options = [
    {
      name: "\uD83D\uDE00",
      handler: props.actionProvider.handleButtons,
      id: 40,
      userID: props.userState,
      sessionID: props.sessionID,
      userInputType: "Feeling",
    },
    {
      name: "\uD83D\uDE10",
      handler: props.actionProvider.handleButtons,
      id: 41,
      userID: props.userState,
      sessionID: props.sessionID,
      userInputType: "Feeling",
    },
    {
      name: "\uD83D\uDE41",
      handler: props.actionProvider.handleButtons,
      id: 42,
      userID: props.userState,
      sessionID: props.sessionID,
      userInputType: "Feeling",
    },
  ];

  return <Options options={options} />;
};
export default FeelingOptions;
