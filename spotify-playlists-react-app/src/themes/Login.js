import { defaultTheme } from "./Spotify";

let particleConfig = {
  num: [4, 7],
  rps: 0.1,
  radius: [5, 40],
  life: [1.5, 3],
  v: [2, 3],
  tha: [-40, 40],
  alpha: [0.6, 0],
  scale: [0.1, 0.4],
  position: "all",
  color: Object.values(defaultTheme.colors),
  cross: "dead",
  // emitter: "follow",
  random: 15,
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
