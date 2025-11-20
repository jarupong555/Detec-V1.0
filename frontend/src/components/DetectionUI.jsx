import React, { useEffect, useState } from 'react'
import '../styles/DetectionUI.css'

const protoOptions = [
  { value: 'usb', label: 'USB/Webcam' },
  { value: 'rtsp', label: 'RTSP' },
  { value: 'rtmp', label: 'RTMP' },
  { value: 'http', label: 'HTTP' },
  { value: 'hls', label: 'HLS (.m3u8)' }
]

const classOptions = [
  { value: 'person', label: 'Person' },
  { value: 'car', label: 'Car' },
  { value: 'all', label: 'All (Person + Car)' }
]

export default function DetectionUI() {
  const [cams, setCams] = useState([])
  const [form, setForm] = useState({ name: '', location: '', protocol: 'rtsp', source: '', detect_classes: 'person' })

  const load = async () => {
    const r = await fetch('/api/cameras')
    const j = await r.json()
    setCams(j)
  }

  useEffect(() => { load() }, [])

  const onChange = e => setForm({ ...form, [e.target.name]: e.target.value })

  const add = async e => {
    e.preventDefault()
    const payload = {
      ...form,
      detect_classes: form.detect_classes === 'all' ? 'person,car' : form.detect_classes
    }

    const r = await fetch('/api/cameras', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (r.ok) {
      setForm({ name: '', location: '', protocol: 'rtsp', source: '', detect_classes: 'person' })
      load()
    } else {
      alert('เพิ่มกล้องไม่สำเร็จ')
    }
  }

  const delCam = async id => {
    if (!confirm('ลบกล้องนี้?')) return
    await fetch('/api/cameras/' + id, { method: 'DELETE' })
    load()
  }

  return (
    <div className="detect-ui">
      <section className="card">
        <h2>เพิ่มกล้อง</h2>
        <form onSubmit={add} className="form-grid">
          <input name="name" value={form.name} onChange={onChange} required placeholder="ชื่อกล้อง" />
          <input name="location" value={form.location} onChange={onChange} placeholder="โลเคชัน" />
          <select name="protocol" value={form.protocol} onChange={onChange}>
            {protoOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <input name="source" value={form.source} onChange={onChange} required placeholder="ลิ้ง/พาธวิดีโอ เช่น rtsp://..., /dev/video0 หรือ 0" />

          {/* Dropdown สำหรับ class */}
          <select name="detect_classes" value={form.detect_classes} onChange={onChange}>
            {classOptions.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>

          <button type="submit">เพิ่ม</button>
        </form>
      </section>

      <section className="card">
        <h2>รายการกล้อง</h2>
        <div className="cams-grid">
          {cams.map(c => (
            <div key={c.id} className="cam-card">
              <div className="cam-head">
                <div>
                  <b>{c.name}</b>
                  <div className="muted">{c.location || '-'}</div>
                </div>
                <button onClick={() => delCam(c.id)}>ลบ</button>
              </div>
              <div className="stream-box">
                <img src={c.stream_url} alt={c.name} />
              </div>
              <div className="muted">Protocol: {c.protocol} • Classes: {c.detect_classes || '(ไม่ตั้งค่า)'}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
