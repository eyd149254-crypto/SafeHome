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

// Background
messaging.onBackgroundMessage((payload) => {
  console.log("[SW] Background message reçu:", payload);
  self.registration.showNotification(
    payload.notification?.title || "Alerte",
    {
      body: payload.notification?.body || "",
      icon: "/static/icon.png",
      badge: "/static/icon.png"
    }
  );
});

// Foreground aussi via SW
self.addEventListener("push", (event) => {
  console.log("[SW] Push reçu:", event);
  const data = event.data?.json() || {};
  const title = data.notification?.title || "Alerte";
  const body  = data.notification?.body  || "";
  event.waitUntil(
    self.registration.showNotification(title, { body })
  );
});