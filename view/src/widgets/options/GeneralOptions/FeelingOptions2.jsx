import React from "react";
import Options from "../Options/Options";

const FeelingOptions2 = (props) => {
  const options = [
    {
      name: "\uD83D\uDE00",
      handler: props.actionProvider.handleButtons,
      id: 43,
      userID: props.userState,
      sessionID: props.sessionID,
      userInputType: "Feeling2",
    },
    {
      name: "\uD83D\uDE41",
      handler: props.actionProvider.handleButtons,
      id: 44,
      userID: props.userState,
      sessionID: props.sessionID,
      userInputType: "Feeling2",
    },
  ];

  return <Options options={options} />;
};
export default FeelingOptions2;
