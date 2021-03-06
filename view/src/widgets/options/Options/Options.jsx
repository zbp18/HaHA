import React from "react";

import styles from "./Options.module.css";
import vase from "../../../images/gestalt vase.png";

const Options = ({ options }) => {
  const runHandler = (handler, userID, sessionID, userInput, userInputType) => {
    handler(userID, sessionID, userInput, userInputType);
  };
  const markup = options.map((option) => (
    <button
      key={option.id}
      className={option.userInputType === "Feeling" || option.userInputType === "Feeling2" ? styles.emoji : styles.option}
      onClick={() =>
        runHandler(
          option.handler,
          option.userID,
          option.sessionID,
          option.name,
          option.userInputType
        )
      }
    >
      {option.userInputType === "Image" ?
        <figure>
          <img src={vase} width={128} alt="Gestalt Vase" />
          <figcaption>Click to continue</figcaption>
        </figure> :
        (option.name === "opening..." ?
          <a href="https://www.doc.ic.ac.uk/~ae/papers/SIHP.pdf" target="_blank">Open the protocols pdf</a>
          : option.name)}
    </button>
  ));
  return <div className={styles.options}>{markup}</div>;
};

export default Options;
