// Generate the mock server keypair (X25519 for ECDH, Ed25519 for signing)
// and verify Node's raw-key <-> KeyObject handling works end to end.
const crypto = require('crypto');
const fs = require('fs');

// Standard DER prefixes for wrapping raw 32-byte keys into KeyObjects.
const X_PRIV_P = Buffer.from('302e020100300506032b656e04220420', 'hex');
const X_PUB_P  = Buffer.from('302a300506032b656e032100', 'hex');
const E_PRIV_P = Buffer.from('302e020100300506032b657004220420', 'hex');
const E_PUB_P  = Buffer.from('302a300506032b6570032100', 'hex');
const rawXPriv = k => crypto.createPrivateKey({ key: Buffer.concat([X_PRIV_P, k]), format: 'der', type: 'pkcs8' });
const rawXPub  = k => crypto.createPublicKey({ key: Buffer.concat([X_PUB_P, k]),  format: 'der', type: 'spki' });
const rawEPriv = k => crypto.createPrivateKey({ key: Buffer.concat([E_PRIV_P, k]), format: 'der', type: 'pkcs8' });
const pubOf = ko => ko.export({ type: 'spki', format: 'der' }).slice(-32);

const xk = crypto.generateKeyPairSync('x25519');
const ek = crypto.generateKeyPairSync('ed25519');
const xpriv = xk.privateKey.export({ type: 'pkcs8', format: 'der' }).slice(-32);
const xpub  = xk.publicKey.export({ type: 'spki', format: 'der' }).slice(-32);
const epriv = ek.privateKey.export({ type: 'pkcs8', format: 'der' }).slice(-32);
const epub  = ek.publicKey.export({ type: 'spki', format: 'der' }).slice(-32);

// Sanity check against the harness's deterministic client (priv = 0x11..0x30).
const clientPriv = Buffer.from(Array.from({ length: 32 }, (_, i) => 0x11 + i));
const clientPub  = pubOf(rawXPriv(clientPriv)); // base * clientPriv
const shared = crypto.diffieHellman({ privateKey: rawXPriv(xpriv), publicKey: rawXPub(clientPub) });
const sig = crypto.sign(null, Buffer.from('hello'), rawEPriv(epriv));

const keys = {
  x25519_priv: xpriv.toString('hex'), x25519_pub: xpub.toString('hex'),
  ed25519_priv: epriv.toString('hex'), ed25519_pub: epub.toString('hex'),
};
fs.writeFileSync(__dirname + '/mockkeys.json', JSON.stringify(keys, null, 2));
console.log('mock keys ->', JSON.stringify(keys, null, 2));
console.log('harness client_pub:', clientPub.toString('hex'));
console.log('shared(mockX, clientPub):', shared.toString('hex'), 'len', shared.length);
console.log('ed sign len:', sig.length);
