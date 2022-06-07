import React from "react";
import { Chatbot } from "react-chatbot-kit";
import "./App.css";
import MessageParser from "./MessageParser";
import ActionProvider from "./ActionProvider";
import config from "./config";
// import MoreInfoDocs from "./widgets/docs/MoreInfoDocs";
import { BrowserView, MobileView, isMobile } from 'react-device-detect';

function App() {
  const ProtocolViewer = () => {
    return (
      <div>
        <BrowserView>
          <div className="box">
            <div
              className="boxstyle">
              Protocol
              viewer</div>
            <iframe id="iframe" allowtransparency="true" className="viewerstyle"
              src="SIHprotocols.pdf#toolbar=0&navpanes=0&scrollbar=0&view=FitW" frameborder="0" position="left">
            </iframe>
          </div>
        </BrowserView >
        <MobileView>
        </MobileView>
      </div >
    );
  };

  return (
    <div className="App">
      <header className={isMobile ? "app-chatbot-container-mobile" : "app-chatbot-container"}>
        <Chatbot
          config={config}
          messageParser={MessageParser}
          actionProvider={ActionProvider}
        />
      </header>
      <ProtocolViewer />
      {/* <MoreInfoDocs className="more-info" /> */}
    </div>
  );
}

export default App;
