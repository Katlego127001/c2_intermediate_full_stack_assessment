/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: "jsdom",
  setupFilesAfterEach: ["<rootDir>/jest.setup.ts"],
  moduleNameMapper: { "^@/(.*)$": "<rootDir>/$1" },
  transform: { "^.+\\.(ts|tsx)$": ["babel-jest", { presets: ["next/babel"] }] },
  testPathIgnorePatterns: ["/node_modules/", "/.next/"],
};
