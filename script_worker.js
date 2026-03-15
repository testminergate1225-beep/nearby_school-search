self.onmessage = function (event) {
    const data = event.data;
    const address = data.address;
    const radius = data.radius;

    // Send the address and radius to Python script using iframe postMessage
    const iframe = document.createElement('iframe');
    iframe.src = '/search.py?address=' + encodeURIComponent(address) + '&radius=' + encodeURIComponent(radius);
    iframe.style.display = 'none';
    document.body.appendChild(iframe);
};
