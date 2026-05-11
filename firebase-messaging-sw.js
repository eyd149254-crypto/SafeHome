importScripts("https://www.gstatic.com/firebasejs/12.12.1/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/12.12.1/firebase-messaging-compat.js");

firebase.initializeApp({
  apiKey: "AIzaSyBwwPXui9YFDHdC21Xr4TqMgBn_VZQRdfs",
  authDomain: "safehome-22c06.firebaseapp.com",
  projectId: "safehome-22c06",
  storageBucket: "safehome-22c06.appspot.com",
  messagingSenderId: "913484933430",
  appId: "1:913484933430:web:947abd3b5888d93b312b97"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {

  console.log(
    "[firebase-messaging-sw.js] Background message ",
    payload
  );

  const notificationTitle =
    payload.notification?.title || "Alerte";

  const notificationOptions = {
    body:
      payload.notification?.body || "Nouvelle alerte",
    icon: "/static/icon.png"
  };

  self.registration.showNotification(
    notificationTitle,
    notificationOptions
  );
});