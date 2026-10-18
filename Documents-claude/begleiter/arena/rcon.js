// Minimaler RCON-Client (Source-RCON-Protokoll) fuer Server-Befehle aus Node
const net = require('net')

class Rcon {
  constructor ({ host, port, passwort }) {
    Object.assign(this, { host, port, passwort })
    this.id = 1
    this.wartend = new Map()
    this.puffer = Buffer.alloc(0)
  }

  verbinden () {
    return new Promise((resolve, reject) => {
      this.sock = net.connect(this.port, this.host)
      this.sock.on('error', reject)
      this.sock.on('data', d => this.lesen(d))
      this.sock.on('connect', async () => {
        try {
          await this.senden(3, this.passwort)
          resolve(this)
        } catch (e) { reject(e) }
      })
    })
  }

  lesen (d) {
    this.puffer = Buffer.concat([this.puffer, d])
    while (this.puffer.length >= 4) {
      const len = this.puffer.readInt32LE(0)
      if (this.puffer.length < len + 4) break
      const id = this.puffer.readInt32LE(4)
      const text = this.puffer.toString('utf8', 12, len + 2)
      this.puffer = this.puffer.subarray(len + 4)
      if (id === -1) { for (const w of this.wartend.values()) w.reject(new Error('RCON-Passwort falsch')); this.wartend.clear(); continue }
      const w = this.wartend.get(id)
      if (w) { this.wartend.delete(id); w.resolve(text) }
    }
  }

  senden (typ, text) {
    const id = this.id++
    const body = Buffer.from(text, 'utf8')
    const paket = Buffer.alloc(14 + body.length)
    paket.writeInt32LE(10 + body.length, 0)
    paket.writeInt32LE(id, 4)
    paket.writeInt32LE(typ, 8)
    body.copy(paket, 12)
    return new Promise((resolve, reject) => {
      this.wartend.set(id, { resolve, reject })
      this.sock.write(paket)
      setTimeout(() => { if (this.wartend.delete(id)) reject(new Error(`RCON-Timeout: ${text}`)) }, 10000)
    })
  }

  befehl (cmd) { return this.senden(2, cmd.replace(/^\//, '')) }
  schliessen () { this.sock?.end() }
}

module.exports = { Rcon }
