const https = require('https');

https.get('https://careerdna-frontend.onrender.com', (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    const match = data.match(/src="(\/assets\/index-[^"]+\.js)"/);
    if (!match) {
      console.log("NO JS FILE FOUND");
      return;
    }
    const jsUrl = 'https://careerdna-frontend.onrender.com' + match[1];
    https.get(jsUrl, (jsRes) => {
      let jsData = '';
      jsRes.on('data', chunk => jsData += chunk);
      jsRes.on('end', () => {
         console.log("JS DOWNLOADED. LENGTH:", jsData.length);
         try {
           new Function(jsData);
           console.log("SYNTAX OK");
         } catch(e) {
           console.log("SYNTAX ERROR:", e.message);
         }
      });
    });
  });
});
