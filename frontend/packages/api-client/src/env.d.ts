declare namespace NodeJS {
  interface ProcessEnv {
    [key: string]: string | undefined;
    NEXT_PUBLIC_API_URL?: string;
    NEXT_PUBLIC_KEYCLOAK_URL?: string;
    NEXT_PUBLIC_KEYCLOAK_REALM?: string;
    NEXT_PUBLIC_KEYCLOAK_CLIENT_ID?: string;
    NEXT_PUBLIC_TILE_URL?: string;
    NEXT_PUBLIC_GEO_API_URL?: string;
  }
}

declare const process: {
  env: NodeJS.ProcessEnv;
};

declare module 'keycloak-js' {
  const Keycloak: any;
  export default Keycloak;
}