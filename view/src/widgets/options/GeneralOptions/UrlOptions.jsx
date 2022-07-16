import React from "react";
import Options from "../Options/Options";

const UrlOptions = (props) => {
  const options = [
    {
      name: "opening...",
      handler: props.actionProvider.handleButtons,
      id: 51,
      userID: props.userState,
      sessionID: props.sessionID,
      userInputType: "Url",
    },
    {
      name: "Continue",
      handler: props.actionProvider.handleButtons,
      id: 52,
      userID: props.userState,
      sessionID: props.sessionID,
      userInputType: "Url",
    },
  ];

  return <Options options={options} />;
};
export default UrlOptions;
