export class ComponentsService {
    #app;
    #registry;
    #factory;
    #blueprints;

    constructor({ app, registry, factory, blueprints }) {
        this.#app = app;
        this.#registry = registry;
        this.#factory = factory;
        this.#blueprints = blueprints;
    }

    definitions(options = {}) {
        return this.#registry.list(options);
    }

    definition(type, options = {}) {
        return this.#registry.get(type, options);
    }

    supports(type, capability) {
        return this.#registry.supports(type, capability);
    }

    create(type, overrides = {}, context = {}) {
        return this.#factory.create(type, overrides, context);
    }

    createBlueprint(id, context = {}) {
        return this.#blueprints.create(id, context);
    }

    insert(canvasId, typeOrBlueprint, options = {}) {
        const asBlueprint = options.blueprint === true;
        const node = asBlueprint
            ? this.createBlueprint(typeOrBlueprint, options.context)
            : this.create(typeOrBlueprint, options.overrides, options.context);

        this.#app.updateDocument((document) => {
            const canvas = document.canvases.find((item) => item.id === canvasId);
            if (!canvas) throw new Error(`Lienzo no encontrado: ${canvasId}`);
            canvas.nodes = Array.isArray(canvas.nodes) ? canvas.nodes : [];
            canvas.nodes.push(node);
        }, {
            label: options.label || `Agregar ${node.name || node.type}`,
            source: "components",
            mergeKey: null,
        });
        return node;
    }
}
