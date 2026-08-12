"use client";

import Script from "next/script";
import { useCallback, useEffect, useLayoutEffect, useRef } from "react";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string }) => void;
          }) => void;
          renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void;
        };
      };
    };
  }
}

/**
 * Renders Google's own "Sign in with Google" button via Google Identity
 * Services. On success it hands the ID token to `onCredential`, which
 * the calling page exchanges for our own JWT pair at /auth/google/.
 * If NEXT_PUBLIC_GOOGLE_CLIENT_ID isn't set, renders nothing rather
 * than a broken button — email auth still works standalone.
 */
export function GoogleSignInButton({ onCredential }: { onCredential: (idToken: string) => void }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const renderedRef = useRef(false);
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  // Kept in a ref so the render callback always calls the latest
  // handler without needing to re-run initialize()/renderButton().
  // Updated in a layout effect (not during render) so the ref write
  // itself is never observed mid-render.
  const onCredentialRef = useRef(onCredential);
  useLayoutEffect(() => {
    onCredentialRef.current = onCredential;
  });

  const renderButton = useCallback(() => {
    if (renderedRef.current || !clientId || !containerRef.current || !window.google) return;

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: (response) => onCredentialRef.current(response.credential),
    });
    window.google.accounts.id.renderButton(containerRef.current, {
      theme: "outline",
      size: "large",
      width: 320,
    });
    renderedRef.current = true;
  }, [clientId]);

  // Covers the case where the GSI script (loaded elsewhere, or cached)
  // is already available by the time this component mounts.
  useEffect(() => {
    renderButton();
  }, [renderButton]);

  if (!clientId) return null;

  return (
    <>
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onLoad={renderButton}
      />
      <div ref={containerRef} className="flex justify-center" />
    </>
  );
}
