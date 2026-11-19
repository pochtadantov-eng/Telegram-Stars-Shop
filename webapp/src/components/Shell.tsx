import type { ReactNode } from "react";
import { BackArrow, Chevron } from "./Icons";
import { haptic } from "../lib/telegram";
import { playClick } from "../lib/sound";

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

export function Tile({
  icon,
  title,
  subtitle,
  onClick,
  children,
}: {
  icon: ReactNode;
  title: string;
  subtitle?: string;
  onClick?: () => void;
  children?: ReactNode;
}) {
  return (
    <button
      type="button"
      className="glass tile"
      onClick={() => {
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
}: {
  name: string;
  photo?: string | null;
}) {
  const letter = (name.replace("@", "")[0] || "?").toUpperCase();
  return (
    <div className="avatar">
      {photo ? <img src={photo} alt="" /> : letter}
    </div>
  );
}
