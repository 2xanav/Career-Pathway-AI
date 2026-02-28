import "./App.css";
import { useState } from "react";

function App() {

  const [major, setMajor] = useState("");
  const [genEd, setGenEd] = useState("");
  const [wakeTime, setWakeTime] = useState("");

  return (
    <div className="homepage">
      <nav className="navbar">
        <div className="logo">Pathway AI</div>
        <div className="nav-links">
          <a href="#">Home</a>
          <a href="Schedules.css">Schedules</a>
        </div>
      </nav>

      <section className="hero">
        <h1>Build Your Schedule</h1>
        <p>
          Select your major, gen-ed preferences, and wake-up time below:
        </p>

        <div className="dropdowns">
          {/* Major */}
          <div className="dropdown">
            <label>Major:</label>
            <select value={major} onChange={(e) => setMajor(e.target.value)}>
              <option value="">Select Major</option>
              <option value="cs">Computer Science</option>
              <option value="math">Business</option>
            </select>
          </div>

          {/* Gen-Ed */}
          <div className="dropdown">
            <label>Gen-Ed Preference:</label>
            <select value={genEd} onChange={(e) => setGenEd(e.target.value)}>
              <option value="">Select Gen-Ed</option>
              <option value="humanities">Humanities</option>
              <option value="social">Social Science</option>
              <option value="science">Science</option>
              <option value="arts">Arts</option>
            </select>
          </div>

          {/* Wake Up Time */}
          <div className="dropdown">
            <label>Wake-Up Time:</label>
            <select value={wakeTime} onChange={(e) => setWakeTime(e.target.value)}>
              <option value="">Select Time</option>
              <option value="6am">6:00 AM</option>
              <option value="7am">7:00 AM</option>
              <option value="8am">8:00 AM</option>
              <option value="9am">9:00 AM</option>
              <option value="10am">10:00 AM</option>
              <option value="11am">11:00 AM</option>
              <option value="12pm">12:00 PM</option>
              <option value="1pm">1:00 PM</option>
              <option value="2pm">2:00 PM</option>
              <option value="3pm">3:00 PM</option>
            </select>
          </div>
        </div>

        <div className="buttons">
          <button className="primary" onClick={() => alert(`Major: ${major}\nGen-Ed: ${genEd}\nWake-Up: ${wakeTime}`)}>
            Submit
          </button>
        </div>
      </section>
    </div>
  );
}

export default App;