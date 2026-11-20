import { useRef, useState, type ReactNode, type PointerEvent } from "react";
import { BackArrow, Chevron } from "./Icons";
import { haptic } from "../lib/telegram";

export function BrandHead({ title }: { title: string }) {
  return (
    <header className="brand-head">
      <h1>{title}</h1>
      <p>мини-приложение</p>
    </header>
  );
}

export function DraggableLogo({ brand }: { brand: string }) {
  const ref = useRef<HTMLButtonElement>(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const drag = useRef<{
    active: boolean;
    startX: number;
    startY: number;
    ox: number;
    oy: number;
  } | null>(null);

  function onDown(e: PointerEvent) {
    haptic();
    const el = ref.current;
    if (!el) return;
    el.setPointerCapture(e.pointerId);
    drag.current = {
      active: true,
      startX: e.clientX,
      startY: e.clientY,
      ox: offset.x,
      oy: offset.y,
    };
  }

  function onMove(e: PointerEvent) {
    if (!drag.current?.active) return;
    const dx = e.clientX - drag.current.startX;
    const dy = e.clientY - drag.current.startY;
    // только запад→север (влево и вверх), чтобы не тянуть Mini App вниз
    const clampX = (v: number) => Math.max(-32, Math.min(0, v));
    const clampY = (v: number) => Math.max(-32, Math.min(0, v));
    setOffset({
      x: clampX(drag.current.ox + dx),
      y: clampY(drag.current.oy + dy),
    });
  }

  function onUp(e: PointerEvent) {
    if (!drag.current) return;
    drag.current.active = false;
    try {
      ref.current?.releasePointerCapture(e.pointerId);
    } catch {
      /* noop */
    }
    // мягко вернуть на место
    setOffset({ x: 0, y: 0 });
  }

  return (
    <button
      ref={ref}
      type="button"
      className="logo-orb logo-orb-drag"
      aria-label="Logo"
      style={{ transform: `translate(${offset.x}px, ${offset.y}px)` }}
      onPointerDown={onDown}
      onPointerMove={onMove}
      onPointerUp={onUp}
      onPointerCancel={onUp}
    >
      {brand.slice(0, 2).toUpperCase()}
    </button>
  );
}

export function PageHeader({
  title,
  subtitle,
  onBack,
  brand,
}: {
  title: string;
  subtitle?: string;
  onBack: () => void;
  brand: string;
}) {
  return (
    <div className="page-title-row page-title-row-inner">
      <button
        type="button"
        className="back-btn back-btn-lg"
        aria-label="Назад"
        onClick={() => {
          haptic();
          onBack();
        }}
      >
        <BackArrow />
      </button>
      <div className="page-title-text">
        <h2>{title}</h2>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      <DraggableLogo brand={brand} />
    </div>
  );
}

export function TileIcon({ src, alt = "" }: { src: string; alt?: string }) {
  return <img className="tile-icon-img" src={src} alt={alt} draggable={false} />;
}

export function Tile({
  icon,
  title,
  subtitle,
  onClick,
  children,
  large,
  compact,
}: {
  icon: ReactNode;
  title: string;
  subtitle?: string;
  onClick?: () => void;
  children?: ReactNode;
  large?: boolean;
  compact?: boolean;
}) {
  return (
    <button
      type="button"
      className={`glass tile ${large ? "tile-lg" : ""} ${compact ? "tile-sm" : ""}`}
      onClick={() => {
        haptic();
        onClick?.();
      }}
    >
      <div className={`tile-icon ${compact ? "tile-icon-sm" : ""}`}>{icon}</div>
      <div className="tile-body">
        <strong>{title}</strong>
        {subtitle ? <span>{subtitle}</span> : null}
        {children}
      </div>
      <span className="chev">
        <Chevron />
      </span>
    </button>
  );
}

export function Avatar({
  name,
  photo,
  size = 40,
}: {
  name: string;
  photo?: string | null;
  size?: number;
}) {
  const letter = (name.replace("@", "")[0] || "?").toUpperCase();
  return (
    <div className="avatar" style={{ width: size, height: size, fontSize: size * 0.35 }}>
      {photo ? <img src={photo} alt="" /> : letter}
    </div>
  );
}
