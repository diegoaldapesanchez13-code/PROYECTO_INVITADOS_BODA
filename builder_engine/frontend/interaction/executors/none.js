export const noneExecutor = Object.freeze({
    type: "NONE",
    validate() { return []; },
    execute() {
        return Object.freeze({ handled: false, type: "NONE" });
    },
});
