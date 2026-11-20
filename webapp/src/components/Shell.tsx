import type { ReactNode } from "react";
import { BackArrow, Chevron } from "./Icons";
import { haptic } from "../lib/telegram";
import { playClick, unlockSound } from "../lib/sound";

export function BrandHead({ title }: { title: string }) {
  return (
    <header className="brand-head">
      <h1>{title}</h1>
      <p>мини-приложение</p>
    </header>
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
    <div className="page-title-row">
      <button
        type="button"
        className="back-btn"
        aria-label="Назад"
        onClick={() => {
          unlockSound();
          playClick();
          haptic();
          onBack();
        }}
      >
        <BackArrow />
      </button>
      <div>
        <h2>{title}</h2>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      <div className="logo-orb">{brand.slice(0, 2).toUpperCase()}</div>
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
}: {
  icon: ReactNode;
  title: string;
  subtitle?: string;
  onClick?: () => void;
  children?: ReactNode;
  large?: boolean;
}) {
  return (
    <button
      type="button"
      className={`glass tile ${large ? "tile-lg" : ""}`}
      onClick={() => {
        unlockSound();
        playClick();
        haptic();
        onClick?.();
      }}
    >
      <div className="tile-icon">{icon}</div>
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
