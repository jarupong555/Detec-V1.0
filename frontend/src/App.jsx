
import React from 'react'
import DetectionUI from './components/DetectionUI.jsx'
import './styles/App.css'

export default function App(){
  return (
    <div className="app-wrap">
      <header>
        <h1>Face Detect Clean</h1>
        <p>YOLOv8l • บันทึกรูปทุก 5 วิเมื่อเจอคลาสที่เลือก</p>
      </header>
      <DetectionUI />
      <footer>
        <small>Test Detec by NWL</small>
      </footer>
    </div>
  )
}
