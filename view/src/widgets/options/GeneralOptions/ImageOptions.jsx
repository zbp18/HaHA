import React from "react";
import Options from "../Options/Options";

const ImageOptions = (props) => {
  const options = [
    {
      name: "staring...",
      handler: props.actionProvider.handleButtons,
      id: 50,
      userID: props.userState,
      sessionID: props.sessionID,
      userInputType: "Image",
    },
  ];

  return <Options options={options} />;
};
export default ImageOptions;
