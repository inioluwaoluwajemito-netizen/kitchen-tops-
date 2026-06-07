import React, { useRef, useState } from "react";

export default function CompareSlider({ before, after, alt = "comparison" }) {
  const [pos, setPos] = useState(50);
  const wrapRef = useRef(null);

  const onDown = (e) => {
    e.preventDefault();
    const move = (ev) => {
      const rect = wrapRef.current.getBoundingClientRect();
      const x = (ev.touches ? ev.touches[0].clientX : ev.clientX) - rect.left;
      const p = Math.max(0, Math.min(100, (x / rect.width) * 100));
      setPos(p);
    };
    const up = () => {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("touchmove", move);
      window.removeEventListener("mouseup", up);
      window.removeEventListener("touchend", up);
    };
    window.addEventListener("mousemove", move);
    window.addEventListener("touchmove", move);
    window.addEventListener("mouseup", up);
    window.addEventListener("touchend", up);
  };

  return (
    <div className="compare-wrap select-none" ref={wrapRef} data-testid="compare-slider">
      <img src={before} alt={`${alt} before`} draggable={false} />
      <div className="compare-after" style={{ width: `${pos}%` }}>
        <img
          src={after}
          alt={`${alt} after`}
          style={{ width: `${wrapRef.current?.clientWidth || 800}px`, maxWidth: "none" }}
          draggable={false}
        />
      </div>
      <div className="compare-handle" style={{ left: `calc(${pos}% - 1px)` }} onMouseDown={onDown} onTouchStart={onDown} />
      <div className="absolute top-3 left-3 px-2 py-1 bg-black/60 text-xs tracking-widest uppercase text-zinc-300 rounded">
        Before
      </div>
      <div className="absolute top-3 right-3 px-2 py-1 bg-gold/90 text-xs tracking-widest uppercase text-black rounded font-medium">
        After
      </div>
    </div>
  );
}
