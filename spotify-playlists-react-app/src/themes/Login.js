import { defaultTheme } from "./Spotify";

let particleConfig = {
  num: [10, 10],
  rps: 0.075,
  radius: [5, 40],
  life: [3, 5],
  v: [1.5, 2],
  tha: [-360, 360],
  alpha: [0.6, 0],
  scale: [0.1, 0.5],
  position: "center",
  color: Object.values(defaultTheme.colors),
  cross: "bround",
  // emitter: "follow",
  // random: 15,
};

let particleBg = {
  position: "absolute",
  zIndex: -1,
  top: 0,
  left: 0,
  backgroundColor: "black",
};

let loginButton = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
};

export { particleConfig, particleBg, loginButton };
