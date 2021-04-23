# pull official base image
FROM node:14.16.1

# set working directory
WORKDIR /spotify-playlists-react-app

# add `/app/node_modules/.bin` to $PATH
ENV PATH /spotify-playlists-react-app/node_modules/.bin:$PATH

# install app dependencies
COPY package.json ./
COPY package-lock.json ./
RUN npm install
RUN npm install react-scripts -g

# add app
COPY . ./

# start app
CMD ["npm", "start"]
